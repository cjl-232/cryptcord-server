import os

from functools import cached_property
from typing import Annotated

import yaml

from cryptography.fernet import Fernet
from pydantic import AfterValidator, BaseModel, ConfigDict

def _validate_max_plaintext_length(value: int) -> int:
    if value <= 0:
        raise ValueError('Value must be a positive integer')
    return value

type _MaxPlaintextLength = Annotated[
    int,
    AfterValidator(_validate_max_plaintext_length),
]    
    
class _SettingsModel(BaseModel):
    model_config = ConfigDict(validate_default=True)
    max_plaintext_length: _MaxPlaintextLength = 2000

    @cached_property
    def effective_max_plaintext_length(self):
        return ((self.max_plaintext_length // 16) + 1) * 16 - 1

    @cached_property
    def max_ciphertext_length(self):
        fernet_key = Fernet(Fernet.generate_key())
        return len(fernet_key.encrypt(bytes(self.max_plaintext_length)))

def _load_settings():
    # Create the settings file if necessary.
    if not os.path.exists('settings.yaml'):
        with open('settings.yaml', 'w') as _:
            pass
    
    # Load settings from the file.
    with open('settings.yaml', 'r') as file:
        _data = yaml.safe_load(file)
        if isinstance(_data, dict):
            settings = _SettingsModel.model_validate(_data)
        else:
            settings = _SettingsModel.model_validate({})
        
    # Add default values to the file.
    with open('settings.yaml', 'w') as file:
        yaml.safe_dump(settings.model_dump(), file)

    # Return the settings object.
    return settings

settings = _load_settings()