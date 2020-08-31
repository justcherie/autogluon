import logging
import re

import pandas as pd
from pandas import DataFrame, Series

from .abstract import AbstractFeatureGenerator
from .binned import BinnedFeatureGenerator

logger = logging.getLogger(__name__)


# TODO: Add verbose descriptions of each special dtype this generator can create.
class TextSpecialFeatureGenerator(AbstractFeatureGenerator):
    def __init__(self, symbols=None, bin_features=True, post_drop_duplicates=True, **kwargs):
        super().__init__(post_drop_duplicates=post_drop_duplicates, **kwargs)
        if symbols is None:
            symbols = ['!', '?', '@', '%', '$', '*', '&', '#', '^', '.', ':', ' ', '/', ';', '-', '=']
        self.symbols = symbols  # Symbols to generate count and ratio features for.
        if bin_features:
            self._post_generators = [BinnedFeatureGenerator(inplace=True)] + self._post_generators

    def _fit_transform(self, X: DataFrame, **kwargs) -> (DataFrame, dict):
        X_out = self._transform(X)
        type_family_groups_special = dict(
            text_special=list(X_out.columns)
        )
        return X_out, type_family_groups_special

    def _transform(self, X: DataFrame) -> DataFrame:
        return self._generate_features_text_special(X)

    def _infer_features_in(self, X, y=None) -> list:
        text_features = self.feature_metadata_in.type_group_map_special['text']
        return text_features

    def _generate_features_text_special(self, X: DataFrame) -> DataFrame:
        if self.features_in:
            X_text_special_combined = []
            for nlp_feature in self.features_in:
                df_text_special = self._generate_text_special(X[nlp_feature], nlp_feature)
                X_text_special_combined.append(df_text_special)
            X_text_special_combined = pd.concat(X_text_special_combined, axis=1)
        else:
            X_text_special_combined = pd.DataFrame(index=X.index)
        return X_text_special_combined

    def _generate_text_special(self, X: Series, feature: str) -> DataFrame:
        X_text_special: DataFrame = DataFrame(index=X.index)
        X_text_special[feature + '.char_count'] = [self.char_count(value) for value in X]
        X_text_special[feature + '.word_count'] = [self.word_count(value) for value in X]
        X_text_special[feature + '.capital_ratio'] = [self.capital_ratio(value) for value in X]
        X_text_special[feature + '.lower_ratio'] = [self.lower_ratio(value) for value in X]
        X_text_special[feature + '.digit_ratio'] = [self.digit_ratio(value) for value in X]
        X_text_special[feature + '.special_ratio'] = [self.special_ratio(value) for value in X]

        for symbol in self.symbols:
            X_text_special[feature + '.symbol_count.' + symbol] = [self.symbol_in_string_count(value, symbol) for value in X]
            X_text_special[feature + '.symbol_ratio.' + symbol] = X_text_special[feature + '.symbol_count.' + symbol] / X_text_special[feature + '.char_count']
            X_text_special[feature + '.symbol_ratio.' + symbol].fillna(0, inplace=True)

        return X_text_special

    @staticmethod
    def word_count(string):
        return len(string.split())

    @staticmethod
    def char_count(string):
        return len(string)

    @staticmethod
    def special_ratio(string):
        string = string.replace(' ', '')
        if not string:
            return 0
        new_str = re.sub(r'[\w]+', '', string)
        return len(new_str) / len(string)

    @staticmethod
    def digit_ratio(string):
        string = string.replace(' ', '')
        if not string:
            return 0
        return sum(c.isdigit() for c in string) / len(string)

    @staticmethod
    def lower_ratio(string):
        string = string.replace(' ', '')
        if not string:
            return 0
        return sum(c.islower() for c in string) / len(string)

    @staticmethod
    def capital_ratio(string):
        string = string.replace(' ', '')
        if not string:
            return 0
        return sum(1 for c in string if c.isupper()) / len(string)

    @staticmethod
    def symbol_in_string_count(string, character):
        if not string:
            return 0
        return sum(1 for c in string if c == character)
