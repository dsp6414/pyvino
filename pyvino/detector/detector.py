
import os
import cv2
from openvino.inference_engine import IENetwork, IEPlugin
from pyvino.util.config import (DEVICE, MODEL_DIR, MODEL_FP,
                                CPU_EXTENSION, TASKS)


class Detector(object):
    def __init__(self, task, path_config=None, model_dir=None, model_fp=None):
        self.task = task
        self.device = DEVICE
        self._set_model_path(model_dir, model_fp)
        # Read IR
        self.net = IENetwork(model=self.model_xml, weights=self.model_bin)
        # Load Model
        self._set_ieplugin(path_config)
        self._get_io_blob()
        self._get_shape()

    def _set_ieplugin(self, path_config):
        plugin = IEPlugin(device=self.device, plugin_dirs=None)
        if path_config is None:
            path_config = CPU_EXTENSION
        else:
            pass
        if self.device == "CPU":
            plugin.add_cpu_extension(path_config)
        else:
            raise NotImplementedError("Only CPU is supported")
        self.exec_net = plugin.load(network=self.net, num_requests=2)

    def _set_model_path(self, model_dir, model_fp):
        model_name = TASKS[self.task]
        if model_dir is None:
            model_dir = MODEL_DIR
        else:
            assert isinstance(model_dir, str)

        if model_fp is None:
            model_fp = MODEL_FP
        elif model_fp == 'FP16':
            pass
        else:
            raise NotImplementedError

        path_model_dir = os.path.join(model_dir, model_name, model_fp)
        self.model_xml = os.path.join(
            path_model_dir, model_name + '.xml')
        self.model_bin = os.path.join(
            path_model_dir, model_name + ".bin")

    def _get_io_blob(self):
        self.input_blob = next(iter(self.net.inputs))
        self.out_blob = next(iter(self.net.outputs))
    
    def _get_shape(self):
        """get shape for network input

        """
        self.shape = self.net.inputs[self.input_blob].shape

    def _in_frame(self, frame):
        """
        transform frame for network input shape
        """
        n, c, h, w = self.shape
        in_frame = cv2.resize(frame, (w, h))
        in_frame = in_frame.transpose((2, 0, 1))
        in_frame = in_frame.reshape((n, c, h, w))
        return in_frame

    def get_result(self, frame):
        in_frame = self._in_frame(frame)
        self.exec_net.start_async(request_id=0, inputs={self.input_blob: in_frame})
        if self.exec_net.requests[0].wait(-1) == 0:
            result = self.exec_net.requests[0].outputs
        return result
