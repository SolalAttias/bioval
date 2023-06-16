# Bioval
Bioval is a Python package made to provide an easy access to a collection of evaluation metrics for comparing the similarity of two tensors, adapted to different evaluation processes of generative models applied to both natural images and biological images. The package support unconditional generation cases, in which we have no labels separating different classes/conditions, and also supports conditional generation, with metrics adapted to evaluating the appropriateness of the generated images to all the distributions of real conditions. The package also supports distance from the real negative control condition, used in most biological contexts.

The package supports tensors of shape (N, I, H, W, C) or (N, H, W, C) or (N, I, F) or (N, F), where N is the number of classes/conditions, I is the number of instances, H is the height, W is the width, C is the number of channels, and F is the number of features.

## Installation
Bioval can be installed from PyPI using the following command:

```bash
poetry build
pip3 install dist/bioval-{version_number}.tar.gz
```

Pypip installation will be supported soon.

## Available Global Metrics
The following evaluation metrics are available in Bioval:

### IntraClass Conditional Evaluation
This metric measures the top-k similarity between two tensors, both within and across classes. The metric returns the following scores: intra_top1, intra_top5, and intra_top10. In a detailled output context, it also returns the distance matrix between all generated and true conditions, computed according to the chosen distance method.

### InterClass Conditional Evaluation
This metric evaluates the pearson correlation between the distances between generated classes and the distance between real classes. This evaluates if the generated class images keep the same class relationships and distances. This metric returns inter_corr and in a detailled output context, returns also inter_p.

### Distance from Control
This metric evaluates the difference between the distances of both generated class images and real class images from real control compounds, to measure if their relationship with the control compound (DMSO for example) is preserved. The metric returns the mean difference between the distance of real and generated conditions from control, as well as the individual difference for each class in the detailled output. 



## Usage
To use Bioval :

```python
from bioval.metrics.conditional_evaluation import ConditionalEvaluation

topk = ConditionalEvaluation()

# Test on 2D tensors
arr1 = torch.randn(100, 10)
arr2 = torch.randn(100, 10)
print("2D tensors")
start_time = time.time()
print(topk(arr1, arr2, k_range=[1, 5, 10, 20, 50, 100]))
print("Time elapsed: {:.2f}s".format(time.time() - start_time))

# Repeat test on 3D tensors
arr1 = torch.randn(100, 10, 10)
arr2 = torch.randn(100, 10, 10)
print("3D tensors")
start_time = time.time()
print(topk(arr1, arr2, k_range=[1, 5, 10, 20, 50, 100]))
print("Time elapsed: {:.2f}s".format(time.time() - start_time))
```

### Usage 

#### Aggregated 

```python
from bioval.metrics.conditional_evaluation import ConditionalEvaluation

# Create an instance of the ConditionalEvaluation class
topk = ConditionalEvaluation()

# Compute top-k similarity scores between two tensors
arr1 = torch.randn(100, 10)
arr2 = torch.randn(100, 10)
scores = topk(arr1, arr2, k_range=[1, 5, 10, 20, 50, 100])
```

#### Distributed 
```python

from bioval.metrics.conditional_evaluation import ConditionalEvaluation

topk = ConditionalEvaluation(distributed_method='fid') # or 'kid' or 'mmd'
arr1 = torch.randn(30, 20, 10, 10, 3) * 256
arr2 = torch.randn(30, 20, 10, 10, 3) * 256
print(topk(arr1, arr2, k_range=[1, 5, 10],aggregated=False)) # returns a dict of scores
```

### Outputs

#### Aggregated without detailled output

if we call the function : 
```python

topk(arr1, arr2, k_range=[1, 5, 10],detailed_output=False)
```

The shape of the output is : 

```python
{
    'control_score': scalar, 
    'inter_corr': scalar, 
    'intra_top1': scalar, 
    'intra_top5': scalar, 
    'intra_top10': scalar,
}
```

#### Aggregated with detailled output

if we call the function : 

```python

topk(arr1, arr2, k_range=[1, 5, 10],detailed_output=True)
```

The shape of the output is : 
TBD


#### Distributed without detailled output


if we call the function : 

```python

topk(arr1, arr2, k_range=[1, 5, 10],aggregated=False,detailed_output=False)
```

TBD

#### distributed with detailled output with control included


if we call the function : 

```python

topk(arr1, arr2,control, k_range=[1, 5, 10],aggregated=False,detailed_output=True)
```

The shape of the output is : 


```python
{
    'control_score': scalar, 
    'class_control_scores': list of scores, one for each class, 
    'inter_corr': scalar, 
    'inter_p': scalar,p-value of the pearson correlation, 
    'intra_kid': scalar, it can also be intra_fid or intra_mmd if chosen in the distributed_method argument, measured per class,
    'matrix': Tensor, with distances between all real and generated classes using distance method of choice,
    'intra_top1': scalar,
    'intra_top5': scalar,
    'mean_ranks': scalar,
    'exact_matching': scalar,
}
```

## Documentation
Please refer to the docstrings in the code for detailed documentation on each metric.

## Contributing
Contributions are welcome! Please refer to the [Contribute]() file for details on how to contribute to Bioval.

## License
Bioval is licensed under the MIT License. Please refer to the [License]() file for details.
