#!/usr/bin/env python3
import torch
import torch.nn as nn
import pandas as pd
from torch.nn.functional import softmax
import yaml

from opensoundscape.datasets import BinaryFromAudio


def predict(
    model,
    prediction_dataset,
    batch_size=1,
    num_workers=0,
    apply_softmax=False,
    labels_yaml=None,
):
    """ Generate predictions on a dataset from a pytorch model object

    Input:
        model:          A binary torch model, e.g. torchvision.models.resnet18(pretrained=True)
                        - must override classes, e.g. model.fc = torch.nn.Linear(model.fc.in_features, 2)
        prediction_dataset: 
                        a pytorch dataset object that returns tensors, such as datasets.PredictionDataset()                
        batch_size:     The size of the batches (# files) [default: 1]
        num_workers:    The number of cores to use for batch preparation [default: 0]
                        - if 0, it uses the current process rather than creating a new one
        apply_softmax:  Apply a softmax activation layer to the raw outputs of the model
        label_names:    Dictionary of numeric labels to names of each class [default: None]
                        - if None, the dataframe returned will have numeric column names
                        - if dictionary is valid (1 class name per numeric label), the returned dataframe will have class names as column names

    Output:
        A dataframe with the CNN prediction results for each class and each file
    """

    if torch.cuda.is_available():
        device = torch.device("cuda:0")
    else:
        device = torch.device("cpu")
    model.eval()
    model.to(device)

    dataloader = torch.utils.data.DataLoader(
        prediction_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
    )

    # run prediction
    all_predictions = []
    for i, inputs in enumerate(dataloader):
        predictions = model(inputs["X"])
        if apply_softmax:
            softmax_val = softmax(predictions, 1).detach().cpu().numpy()
            for x in softmax_val:
                all_predictions.append(x)
        else:
            for x in predictions.detach().numpy():
                all_predictions.append(list(x))  # .astype('float64')

    img_paths = prediction_dataset.df[prediction_dataset.audio_column].values
    pred_df = pd.DataFrame(index=img_paths, data=all_predictions)

    if labels_yaml is not None:
        pred_df.rename(columns=yaml.load(labels_yaml))

    return pred_df
