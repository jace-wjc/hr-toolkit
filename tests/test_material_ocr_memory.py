from __future__ import annotations

import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from PIL import Image

from hr_toolkit.tools import material_collector as mc


class MaterialOCRMemoryTest(unittest.TestCase):
    def test_serial_preserves_padded_input_and_all_output_shapes(self):
        batch = np.arange(6 * 3 * 48 * 400, dtype=np.float32).reshape(6, 3, 48, 400)
        for container in (list, tuple, np.ndarray):
            calls = []

            def session(value):
                calls.append(value.copy())
                outputs = [value.sum(axis=1), value.mean(axis=1)]
                return outputs[0] if container is np.ndarray else container(outputs)

            expected = session(batch)
            calls.clear()
            result = mc._SerialOCRSession(session)(batch)
            self.assertIsInstance(result, container)
            self.assertEqual(len(calls), 6)
            np.testing.assert_array_equal(np.concatenate(calls), batch)
            self.assertTrue(all(value.shape == (1, 3, 48, 400) for value in calls))
            if container is np.ndarray:
                np.testing.assert_array_equal(result, expected)
            else:
                for actual, original in zip(result, expected):
                    np.testing.assert_array_equal(actual, original)

    def test_sessions_restore_on_error_and_cancel_between_items(self):
        calls = []

        def session(batch):
            calls.append(len(batch))
            return batch

        engine = SimpleNamespace(text_cls=SimpleNamespace(session=session), text_rec=SimpleNamespace(session=session))
        with self.assertRaises(mc.MaterialCollectionCancelled):
            with mc._serial_ocr_sessions(engine, True, lambda: len(calls) >= 1):
                engine.text_rec.session(np.zeros((6, 3, 48, 320)))
        self.assertEqual(calls, [1])
        self.assertIs(engine.text_cls.session, session)
        self.assertIs(engine.text_rec.session, session)
        with self.assertRaises(MemoryError):
            with mc._serial_ocr_sessions(engine, True):
                raise MemoryError()
        self.assertIs(engine.text_rec.session, session)
        with mc._serial_ocr_sessions(engine, False):
            self.assertIs(engine.text_rec.session, session)

    def test_serial_rejects_invalid_result_instead_of_silent_success(self):
        with self.assertRaises(mc.OCRUnavailableError):
            mc._SerialOCRSession(lambda batch: np.zeros((2, 4)))(np.zeros((6, 4)))

    def test_a4_budget_and_existing_input_limits(self):
        with Image.new('RGB', (1654, 2339), 'white') as image:
            output = BytesIO()
            image.save(output, format='PNG')
        budget = mc._inspect_ocr_input_budget(output.getvalue())
        self.assertEqual((budget.width, budget.height), (1654, 2339))
        self.assertEqual((budget.normal + 1024**2 - 1) // 1024**2, 2850)
        self.assertLess(budget.serial, 1400 * 1024**2)
        self.assertGreaterEqual(budget.serial, 512 * 1024**2)
        for width, height in ((16, 16), (800, 1100), (3000, 4000)):
            sample = mc._OCRImageBudget(width, height, width * height)
            self.assertLessEqual(sample.serial, sample.normal)
        with patch.object(mc, '_OCR_MAX_INPUT_BYTES', 1):
            with self.assertRaises(mc.OCRResourceLimitError):
                mc._inspect_ocr_input_budget(output.getvalue())
        with patch.object(mc, '_OCR_MAX_INPUT_PIXELS', 1):
            with self.assertRaises(mc.OCRResourceLimitError):
                mc._inspect_ocr_input_budget(output.getvalue())

    def test_low_memory_selects_serial_normal_and_unknown_memory_keep_original(self):
        budget = mc._OCRImageBudget(1654, 2339, 1440 * 2016)
        for available, expected_serial in ((1400 * 1024**2, True), (8 * 1024**3, False), (None, False)):
            seen = []
            notices = []

            class Engine:
                def __init__(self):
                    self.text_cls = SimpleNamespace(session=lambda batch: batch)
                    self.text_rec = SimpleNamespace(session=lambda batch: batch)

                def __call__(self, source):
                    seen.append(isinstance(self.text_rec.session, mc._SerialOCRSession))
                    return [([], '保持原结果', 0.99)], 0.1

            engine = Engine()
            with self.subTest(available=available), patch.object(mc, '_available_ocr_memory', return_value=available), patch.object(mc, '_inspect_ocr_input_budget', return_value=budget), patch.object(mc, '_get_ocr_engine', return_value=engine), patch.object(mc, '_log_ocr_budget'):
                result = mc._collect_ocr_texts(Path('原始资料.png'), progress_callback=lambda *args: notices.append(args))
            self.assertEqual(result, (['保持原结果'], True))
            self.assertEqual(seen, [expected_serial])
            self.assertEqual(len(notices), int(expected_serial))
            self.assertFalse(isinstance(engine.text_rec.session, mc._SerialOCRSession))

    def test_pressure_after_engine_start_and_unknown_adapter_still_stop(self):
        budget = mc._OCRImageBudget(1654, 2339, 1440 * 2016)
        for supported in (True, False):
            engine = SimpleNamespace(text_cls=SimpleNamespace(session=lambda b: b), text_rec=SimpleNamespace(session=lambda b: b)) if supported else object()
            readings = [1400 * 1024**2, 700 * 1024**2, 700 * 1024**2]
            with self.subTest(supported=supported), patch.object(mc, '_available_ocr_memory', side_effect=readings), patch.object(mc, '_inspect_ocr_input_budget', return_value=budget), patch.object(mc, '_get_ocr_engine', return_value=engine), patch.object(mc, '_log_ocr_budget'):
                with self.assertRaises(mc.OCRMemoryPressureError):
                    mc._collect_ocr_texts(Path('原始资料.png'))


if __name__ == '__main__':
    unittest.main()
