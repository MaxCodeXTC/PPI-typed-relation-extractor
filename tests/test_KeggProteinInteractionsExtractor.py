import unittest
import os
from unittest.mock import MagicMock

from bioservices import KEGG, UniProt
from ddt import ddt, data, unpack
from logging.config import fileConfig

from dataextractors.KeggProteinInteractionsExtractor import KeggProteinInteractionsExtractor


@ddt
class TestKeggProteinInteractionsExtractor(unittest.TestCase):

    def setUp(self):
        fileConfig(os.path.join(os.path.dirname(__file__), 'logger.ini'))

    @data(("sample_ko.kgml", 4))
    @unpack
    def test_extract_protein_interactions_kgml(self, kgml_file, expected_no_rel):
        # Arrange
        sut = KeggProteinInteractionsExtractor()
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), kgml_file), 'r') as myfile:
            kgml_string = myfile.read()

        # Mock Kegg ops
        mock_kegg = KEGG()
        sut.kegg = mock_kegg

        # No matter what the input is, return the  ko numbers that map to hsa numbers
        mock_kegg.link = MagicMock(return_value="ko:K00922	hsa:5293\n" +
                                                "ko:K00922	hsa:5291\n" +
                                                "ko:K02649	hsa:5295")

        # No matter what the input is, return the  hsa numbers that map to uniprot numbers
        mock_kegg.conv =  MagicMock(return_value = {"hsa:5293" : "up:B0LPE5"})

        # Mock Uni Prot
        mock_uniprot =  UniProt()
        sut.uniprot = mock_uniprot
        mock_uniprot.mapping = MagicMock(return_value = {"B0LPE5": ["gene1", "gene2"]})

        # Act
        actual = sut.extract_protein_interactions_kgml(kgml_string)

        # Assert
        self.assertEqual(expected_no_rel, len(actual))
