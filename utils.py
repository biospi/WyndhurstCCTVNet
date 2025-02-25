import paramiko
import os
import time
from pathlib import Path
import configparser
import pandas as pd
from datetime import datetime


def is_float(string):
    try:
        float(string)
        if '.' not in string:
            return False
        return True
    except ValueError:
        return False

