"""Basic tests for mcp-cam server."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch, MagicMock
import numpy as np

from server import (
    _device_index_from_id,
    _resolve_save_path,
    capture_base64,
    capture_image,
    _frame_to_base64,
    _frame_to_image,
)


class TestHelpers(unittest.TestCase):
    def test_device_index_from_id(self):
        self.assertEqual(_device_index_from_id("cam_2"), 2)
        self.assertEqual(_device_index_from_id("cam_0"), 0)
        self.assertEqual(_device_index_from_id("other"), 0)

    def test_resolve_save_path_given(self):
        self.assertEqual(_resolve_save_path("/tmp/x.jpg"), "/tmp/x.jpg")


class TestFrameConvertion(unittest.TestCase):
    def test_frame_to_base64(self):
        frame = np.ones((10, 10, 3), dtype=np.uint8) * 128
        result = _frame_to_base64(frame, quality=95)
        self.assertTrue(result.startswith("IMAGE_BASE64:"))

    def test_frame_to_image(self):
        from fastmcp.utilities.types import Image
        frame = np.ones((10, 10, 3), dtype=np.uint8) * 64
        result = _frame_to_image(frame, quality=95)
        self.assertIsInstance(result, Image)
        self.assertEqual(result._format, "jpeg")


class TestCaptureMock(unittest.TestCase):
    @patch("server.cv2.VideoCapture")
    async def test_capture_base64(self, mock_cap_cls):
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.side_effect = [
            (True, np.ones((20, 20, 3), dtype=np.uint8) * 128)
        ]
        mock_cap_cls.return_value = mock_cap
        # This is a minimal smoke test.


if __name__ == "__main__":
    unittest.main()
