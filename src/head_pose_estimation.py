"""
This is a sample class for a model. You may choose to use it as-is or make any changes to it.
This has been provided just to give you an idea of how to structure your model class.
"""

import os  # used to split the model location string
import cv2
import numpy as np
import logging as log
from openvino.inference_engine import IECore  # used to load the IE python API


class HeadPoseEstimationModel:
    """
            Class for the Face Detection Model.
    """

    def __init__(self, model_name, device="CPU", extensions=None):
        """
                This method intends to initialize all the attributes of the class
        :param model_name: The name of model .xml file
        :param device: Device Type(CPU/GPU/VPU/GPGA)
        :param extensions: CPU extension path
        """
        self.model = model_name
        self.device = device
        self.extension = extensions
        self.ie = None
        self.net = None
        self.inp = None
        self.out = None
        self.ext = None
        self.ex_net = None
        self.supported = None
        self.input_shape = None
        self.output_shape = None

    def load_model(self):
        """
                This method is for loading the model to the device specified by the user.
                If your model requires any Plugins, this is where we can load them.
        :return: None
        """
        self.ie = IECore()
        model_xml = self.model
        model_bin = os.path.splitext(model_xml)[0] + ".bin"
        self.net = self.ie.read_network(model=model_xml, weights=model_bin)
        self.ex_net = self.ie.load_network(network=self.net, device_name=self.device)

        self.check_cpu_support()

        # to get the shape of input and output and set each to a class variable
        self.inp = next(iter(self.net.inputs))
        self.out = next(iter(self.net.outputs))

    def check_cpu_support(self):
        """
                This function intends to add the extension if CPU support is needed
        :return: None
        """
        unsupported = self.supported_layers
        if len(unsupported) != 0 and "CPU" in self.device:
            if self.extension is None:
                log.error(
                    "please provide the link to CPU extension, in order to run unsupported layers"
                )
                exit(1)
            else:
                self.ie.add_extension(self.extension, "CPU")
                unsupported = self.supported_layers
                if len(unsupported) != 0:
                    log.error(
                        "Needs to exit, as some layers were unable to run on CPU as well"
                    )
                else:
                    exit(1)

    @property
    def supported_layers(self):
        """
                this function intends to find the unsupported layers on the given device
        :return: list of unsupported layers
        """
        self.supported = self.ie.query_network(
            network=self.net, device_name=self.device
        )
        unsupported_layers = [
            layer for layer in self.net.layers.keys() if layer not in self.supported
        ]
        return unsupported_layers

    def get_input_shape(self):
        """
                This method intends to set the input shape parameter
        :return: None
        """
        self.input_shape = self.net.inputs[self.inp].shape

    def get_output_shape(self):
        """
                This method intends to set the input shape parameter
        :return: None
        """
        self.output_shape = self.net.outputs[self.out].shape

    def predict(self, image, flag):
        """
                This method is meant for running predictions on the input image.
        :param image:
        :return: processed output
        """
        self.get_input_shape()
        self.get_output_shape()
        proc_img = self.preprocess_input(image.copy())
        out_put = self.ex_net.infer({self.inp: proc_img})
        proc_out = self.preprocess_output(out_put)
        if flag == 3:
            perf = self.ex_net.requests[0].get_perf_counts()
            return proc_out, perf
        else:
            return proc_out, {}

    def preprocess_output(self, outputs):
        """
                Before feeding the output of this model to the next model,
                we might have to preprocess it.
        :param outputs: inference output
        :return: contour points of the head
        """
        cnt = [
            outputs["angle_y_fc"].tolist()[0][0],
            outputs["angle_p_fc"].tolist()[0][0],
            outputs["angle_r_fc"].tolist()[0][0],
        ]
        return cnt

    def preprocess_input(self, image):
        """
                Before feeding the data into the model for inference,
                we might have to preprocess it.
        :param image: RGB image
        :return: processed BGR image
        """
        proc_image = cv2.resize(image, (self.input_shape[3], self.input_shape[2]))
        proc_image = np.transpose(np.expand_dims(proc_image, axis=0), (0, 3, 1, 2))
        return proc_image
