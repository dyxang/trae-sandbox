import yaml


DEFAULT_CONFIG = {
    "input_file": None,
    "output_file": None,
    "target_discount_pct": None,
    "tolerance": 0.01,
    "max_float_large": 0.01,
    "max_float_medium": 0.02,
    "max_float_small": 0.03,
    "random_seed": 42,
    "up_down_ratio": "auto",
    "correlation_max": 0.5,
    "gini_max": 0.25,
}


class Config:
    def __init__(self, config_path=None):
        self._config = dict(DEFAULT_CONFIG)
        if config_path is not None:
            self.load(config_path)

    def load(self, config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f)
        if user_config and isinstance(user_config, dict):
            self._config.update(user_config)
        return self

    def get(self, key):
        return self._config.get(key)

    def validate(self):
        errors = []

        discount = self._config.get("target_discount_pct")
        if discount is not None:
            if not isinstance(discount, (int, float)):
                errors.append("target_discount_pct 必须为数值")
            elif discount < 0 or discount > 100:
                errors.append("target_discount_pct 必须在 0~100 之间")

        tolerance = self._config.get("tolerance")
        if tolerance is not None:
            if not isinstance(tolerance, (int, float)) or tolerance <= 0:
                errors.append("tolerance 必须为正数")

        for key in ("max_float_large", "max_float_medium", "max_float_small"):
            val = self._config.get(key)
            if val is not None:
                if not isinstance(val, (int, float)) or val <= 0 or val > 1:
                    errors.append(f"{key} 必须在 (0, 1] 之间")

        seed = self._config.get("random_seed")
        if seed is not None:
            if not isinstance(seed, int):
                errors.append("random_seed 必须为整数")

        gini_max = self._config.get("gini_max")
        if gini_max is not None:
            if not isinstance(gini_max, (int, float)) or gini_max <= 0 or gini_max > 1:
                errors.append("gini_max 必须在 (0, 1] 之间")

        correlation_max = self._config.get("correlation_max")
        if correlation_max is not None:
            if not isinstance(correlation_max, (int, float)) or correlation_max <= 0 or correlation_max > 1:
                errors.append("correlation_max 必须在 (0, 1] 之间")

        return errors
