"""
Basic import tests for TradeEngine
"""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_flask_imports():
    """Test Flask and related imports"""
    try:
        import flask
        from flask import Flask
        from flask_socketio import SocketIO
        from flask_sqlalchemy import SQLAlchemy
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import Flask modules: {e}")


def test_data_processing_imports():
    """Test data processing library imports"""
    try:
        import pandas as pd
        import numpy as np
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import data processing modules: {e}")


def test_database_imports():
    """Test database library imports"""
    try:
        import sqlalchemy
        from sqlalchemy import create_engine
        assert True
    except ImportError as e:
        pytest.fail(f"Failed to import database modules: {e}")


def test_python_version():
    """Test Python version compatibility"""
    assert sys.version_info >= (3, 8), "Python 3.8+ required"


def test_pandas_functionality():
    """Test basic pandas functionality"""
    import pandas as pd
    df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
    assert len(df) == 3
    assert list(df.columns) == ['A', 'B']


def test_numpy_functionality():
    """Test basic numpy functionality"""
    import numpy as np
    arr = np.array([1, 2, 3, 4, 5])
    assert len(arr) == 5
    assert arr.mean() == 3.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
