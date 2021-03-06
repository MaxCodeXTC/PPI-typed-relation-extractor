import tempfile
from io import StringIO
from unittest import TestCase
from unittest.mock import MagicMock

from algorithms import TrainInferencePipeline
from algorithms.TrainInferenceBuilder import TrainInferenceBuilder


class TestTrainInferenceBuilder(TestCase):
    def test_get_trainpipeline(self):
        # Arrange
        mock_dataset = MagicMock()
        mock_scorer = MagicMock()
        mock_scorer.return_value = 1
        mock_dataset.data = [[["This is sample text", "entity1", "entity2", "phosphorylation"], ["yes"]],
                             [["This is sample text2", "entity1", "entity2", "phosphorylation"], ["no"]]]
        mock_dataset.feature_lens = [100, 1, 1, 1]
        mock_dataset.class_size = 2

        mock_dataset.__len__.return_value = len(mock_dataset.data)
        mock_dataset.__getitem__.side_effect = lambda i: (mock_dataset.data[i][0], mock_dataset.data[i][1])

        embedding = StringIO(
            "\n".join(["4 4", "hat 0.2 .34 0.8", "mat 0.5 .34 0.8", "entity1 0.5 .55 0.8", "entity2 0.3 .55 0.9"]))

        out_dir = tempfile.mkdtemp()

        sut = TrainInferenceBuilder(dataset=mock_dataset, embedding_handle=embedding, output_dir=out_dir,
                                    model_dir=out_dir,
                                    embedding_dim=3, results_scorer=mock_scorer)

        # Act
        actual = sut.get_trainpipeline()

        # Assert
        self.assertIsInstance(actual, TrainInferencePipeline.TrainInferencePipeline)
