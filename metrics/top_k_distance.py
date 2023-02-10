import torch
import torch.nn as nn
import torch.nn.functional as F


"""
Necessary modifications to the original code:
Modify the distance matrix shape to (d,d)
adapt the topkmatching depending on some rules of the numbers of classes
adapt the topKdistance to work on images too by importing an inception model and running it on it
ajouter le distribué

Input shape : ('batch size', 'number of classes', 'number of features')
"""


class TopKDistance:
    """
    This class computes top K distance between two tensors.

    Parameters
    ----------
    method : str, optional
        The method for computing the distance between the two tensors. The options are 'euclidean', 'cosine',
        'correlation', 'chebyshev', 'minkowski', and 'cityblock'. The default method is 'euclidean'.

    aggregate : str, optional
        The method for aggregating a 3D tensor into a 2D tensor. The options are 'mean', 'median', and 'robust_mean'.
        The default aggregate method is 'mean'.

    Attributes
    ----------
    method : str
        The method for computing the distance between the two tensors.

    aggregate : str
        The method for aggregating a 3D tensor into a 2D tensor.

    _methods : dict
        A dictionary containing all the available methods for computing the distance between the two tensors.

    _aggregs : dict
        A dictionary containing all the available methods for aggregating a 3D tensor into a 2D tensor.
    """
    def __init__(self, method: str = 'euclidean',aggregate: str = 'mean'):
        self.method = method
        self.aggregate = aggregate
        self._methods = {
            'euclidean': self._euclidean,
            'cosine': self._cosine,
            'correlation': self._correlation,
            'chebyshev': self._chebyshev,
            'minkowski': self._minkowski,
            'cityblock': self._cityblock
        }
        self._aggregs = {
            'mean': self._mean,
            'median': self._median,
            'robust_mean': self._robust_mean
        }


    def __call__(self, arr1: torch.Tensor, arr2: torch.Tensor, k_range=[1, 5, 10]) -> dict:
        """
        Computes top K distance between two tensors.

        Parameters
        ----------
        arr1 : torch.Tensor
            The first tensor to be compared. It should be a 2D or 3D tensor.

        arr2 : torch.Tensor
            The second tensor to be compared. It should be a 2D or 3D tensor.

        k_range : list, optional
            A list of values representing the percentage of top K distance to be computed. The default value is
            [1, 5, 10].

        Returns
        -------
        dict
            A dictionary containing the top K distances computed for the specified range of K. The keys are 'topK', where
            K is the value from `k_range`. The values are the top K distances in float format computed for the specified value of K.


        Example
        -------
        >>> arr1 = torch.tensor([[0.7, 0.2, 0.1], [0.3, 0.5, 0.2], [0.1, 0.3, 0.6]])
        >>> arr2 = torch.tensor([[0.7, 0.2, 0.1], [0.3, 0.5, 0.2], [0.1, 0.3, 0.6]])
        >>> top_k_distance = TopKDistance()
        >>> top_k_distance(arr1, arr2)
        {'top1': 100.0, 'top5': 100.0, 'top10': 100.0}
        """
        # check if method and aggregate attributes are valid
        if self.method not in self._methods:
            raise ValueError(f"{self.method} not in list of defined methods. Please choose from {list(self._methods.keys())}")
        if self.aggregate not in self._aggregs:
            raise ValueError(f"{self.aggregate} not in list of defined aggregations. Please choose from {list(self._aggregs.keys())}")
        
        # check if arr1 and arr2 are 2D or 3D tensors and raise error if not
        if arr1.ndim not in [2, 3]:
            raise ValueError(f"arr1 should be a 2D or 3D tensor, but got {arr1.ndim}D tensor")
        if arr2.ndim not in [2, 3]:
            raise ValueError(f"arr2 should be a 2D or 3D tensor, but got {arr2.ndim}D tensor")

        # aggregate the arrays if they are 3D tensors
        if arr1.ndim == 3:
            arr1 = self._aggregs[self.aggregate](arr1)
        if arr2.ndim == 3:
            arr2 = self._aggregs[self.aggregate](arr2)
        # get the matrix for comparison using the specified method
        matrix = self._methods[self.method](arr1, arr2)

        # compute the diagonal ranks of the comparison matrix
        ranks = self._compute_diag_ranks(matrix)
        # compute the scores for each value in k_range
        mean_ranks = torch.mean(ranks.float(), dim=0)
        dict_score = {}
        # compute the scores for each value in k_range
        for k in k_range:
            number_values = matrix.shape[0] * (k/100)
            r = (ranks <= number_values).sum()
            r = (r/matrix.shape[0]) * 100
            dict_score['top'+str(k)] = r
        # add the mean ranks score to the dictionary
        dict_score['mean_ranks'] = (mean_ranks/matrix.shape[0]) * 100
        # add the exact matching score to the dictionary
        r_exact = (ranks == 0).sum()
        dict_score['exact_matching'] = (r_exact/matrix.shape[0]) * 100
        return dict_score
    @staticmethod
    def _compute_diag_ranks(matrix: torch.Tensor) -> torch.Tensor:
        """
        Computes the diagonal ranks of a given matrix.

        Parameters:
        matrix (torch.Tensor): 2D tensor of similarity scores between two arrays.

        Returns:
        torch.Tensor: 1D tensor of ranks of the diagonal elements in the input matrix. 
                    Ranks start from 1, with 1 being the highest score.

        Example:
        >>> matrix = torch.tensor([[0.7, 0.2, 0.1], [0.3, 0.5, 0.2], [0.1, 0.3, 0.6]])
        >>> _compute_diag_ranks(matrix)
        tensor([1, 3, 2])
        """
        # Sort matrix in descending order along each column
        _, indices = torch.sort(matrix, dim=0, descending=True)

        # Initialize ranks tensor with zeros
        ranks = torch.zeros(matrix.shape[0], dtype=torch.int64)

        # Compute the rank of each diagonal element by finding its index
        for i in range(matrix.shape[0]):
            ranks[i] = (indices[:, i] == i).nonzero()[0].item() + 1  # to have index starting at 1

        return ranks



    @staticmethod
    def _euclidean(arr1: torch.Tensor, arr2: torch.Tensor) -> torch.Tensor:
        return torch.norm(arr1[:, None, :] - arr2[None, :, :], p=2, dim=-1)

    @staticmethod
    def _cosine(arr1: torch.Tensor, arr2: torch.Tensor) -> torch.Tensor:
        return 1 - F.cosine_similarity(arr1[:, None, :], arr2[None, :, :], dim=-1)

    @staticmethod
    def _correlation(arr1: torch.Tensor, arr2: torch.Tensor) -> torch.Tensor:
        mean1 = torch.mean(arr1, dim=-1, keepdim=True)
        mean2 = torch.mean(arr2, dim=-1, keepdim=True)
        centered1 = arr1 - mean1
        centered2 = arr2 - mean2
        return 1 - torch.sum(centered1[:, None, :] * centered2[None, :, :], dim=-1) / torch.norm(centered1, p=2, dim=-1) / torch.norm(centered2, p=2, dim=-1)

    @staticmethod
    def _chebyshev(arr1: torch.Tensor, arr2: torch.Tensor) -> torch.Tensor:
        return torch.max(torch.abs(arr1[:, None, :] - arr2[None, :, :]), dim=-1)[0]

    @staticmethod
    def _minkowski(arr1: torch.Tensor, arr2: torch.Tensor, p: float = 3) -> torch.Tensor:
        return torch.norm(arr1[:, None, :] - arr2[None, :, :], p=p, dim=-1)

    @staticmethod
    def _cityblock(arr1: torch.Tensor, arr2: torch.Tensor) -> torch.Tensor:
        return torch.sum(torch.abs(arr1[:, None, :] - arr2[None, :, :]), dim=-1)



    @staticmethod
    def _mean(emb: torch.Tensor) -> torch.Tensor:
        if emb.ndim == 3:
            return torch.mean(emb, dim=1)
        else:
            return emb
    @staticmethod
    def _median(emb: torch.Tensor) -> torch.Tensor:
        if emb.ndim == 3:
            return torch.median(emb, dim=1)[0]
        else:
            return emb
    @staticmethod
    def _robust_mean(emb: torch.Tensor) -> torch.Tensor:
        if emb.ndim == 3:
            log_embeddings = torch.log(emb + 1e-8)
            avg_log_embeddings = torch.mean(log_embeddings, dim=1)
            return torch.exp(avg_log_embeddings)
        else:
            return emb

# test the class
if __name__ == '__main__':
    topk = TopKDistance()
    arr1 = torch.randn(100, 10)
    arr2 = torch.randn(100, 10)
    # convert to float values
    arr1 = arr1.float()
    arr2 = arr2.float()
    print(topk(arr1, arr2, k_range=[1, 5, 10, 20, 50, 100]))