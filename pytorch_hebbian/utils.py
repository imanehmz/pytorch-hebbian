import logging
from typing import List

import numpy as np
import torch
from ignite.utils import convert_tensor
from matplotlib import pyplot as plt
from torch.utils.data import random_split


def plot_to_img(fig):
    """Takes a matplotlib figure handle and converts it using canvas and string-casts to a numpy array that can be
    visualized in TensorBoard using the add_image function
    """
    # Draw figure on canvas
    fig.canvas.draw()

    # Convert the figure to numpy array, read the pixel values and reshape the array
    img = np.fromstring(fig.canvas.tostring_rgb(), dtype=np.uint8, sep='')
    img = img.reshape(fig.canvas.get_width_height()[::-1] + (3,))

    # Normalize into 0-1 range for TensorBoard
    img = img / 255.0
    img = np.transpose(img, (2, 0, 1))

    plt.close(fig)

    return img


def extract_image_patches(x, kernel_size, stride=(1, 1), dilation=1, padding=0):
    # TODO: implement dilation and padding
    # TODO: does the order in which the patches are returned matter?
    b, c, h, w = x.shape

    # Extract patches
    patches = x.unfold(2, kernel_size[0], stride[0]).unfold(3, kernel_size[1], stride[1])
    patches = patches.permute(0, 4, 5, 1, 2, 3).contiguous()

    return patches.view(-1, kernel_size[0], kernel_size[1])


def split_dataset(dataset, val_split):
    val_size = int(val_split * len(dataset))
    train_size = len(dataset) - val_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

    return train_dataset, val_dataset


def prepare_batch(batch, device=None, non_blocking=False):
    """Prepare batch for training: pass to a device with options."""
    x, y = batch
    return (convert_tensor(x, device=device, non_blocking=non_blocking),
            convert_tensor(y, device=device, non_blocking=non_blocking))


def load_weights(model, state_dict_path, layer_names=None, freeze=False):
    """Load model weights from a stored state dict. Optionally only load weights for the specified layer."""
    if torch.cuda.is_available():
        device = 'cuda'
    else:
        device = 'cpu'

    state_dict = torch.load(state_dict_path, map_location=torch.device(device))

    if layer_names is not None:
        state_dict = extract_layers_from_state_dict(state_dict, layers=layer_names)

    model.load_state_dict(state_dict, strict=False)
    logging.info("Loaded initial model weights for layer(s) {} from '{}'.".format(layer_names, state_dict_path))

    if freeze:
        for layer in [dict(model.named_children())[k] for k in layer_names]:
            for param in layer.parameters():
                param.requires_grad = False
        logging.info("Freezed layer(s) {}.".format(layer_names))

    return model


def extract_layers_from_state_dict(state_dict: dict, layers: List[str]):
    """Extract layers from a state dict."""
    layer_weights = ['{}.weight'.format(layer) for layer in layers]
    new_state_dict = {layer_weight: state_dict[layer_weight] for layer_weight in layer_weights}
    return new_state_dict


def get_device(device=None):
    if device is None:
        if torch.cuda.is_available():
            device = 'cuda'
            torch.set_default_tensor_type('torch.cuda.FloatTensor')
        else:
            device = 'cpu'
    elif device == 'cuda':
        if torch.cuda.is_available():
            device = 'cuda'
            torch.set_default_tensor_type('torch.cuda.FloatTensor')
        else:
            device = 'cpu'
    else:
        device = 'cpu'

    if device == 'cuda':
        logging.info("CUDA device set to '{}'.".format(torch.cuda.get_device_name(0)))

    return device
