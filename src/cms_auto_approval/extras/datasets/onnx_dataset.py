from pathlib import PurePosixPath
from kedro.io.core import (
    AbstractVersionedDataSet,
    get_filepath_str,
    get_protocol_and_path,
    Version
)
import fsspec
from typing import Any, Dict
from skl2onnx import convert_sklearn, to_onnx
from skl2onnx.common.data_types import FloatTensorType
import onnxruntime as rt
import onnx

class OnnxDataSet(AbstractVersionedDataSet):

    def __init__(self, filepath: str, version: Version = None):
        protocol, path = get_protocol_and_path(filepath)
        self._protocol = protocol
        self._fs = fsspec.filesystem(self._protocol)

        super().__init__(
            filepath=PurePosixPath(path),
            version=version,
            exists_function=self._fs.exists,
            glob_function=self._fs.glob,
        )

    def _load(self):
        """
        Return model path, which can then be loaded by the clients ONNX runtime session.
        Returning the model directly yields a UTF error message or incompatible type error depending on approach used.
        """
        return get_filepath_str(self._get_load_path(), self._protocol)

    def _save(self, data) -> None:
        # using get_filepath_str ensures that the protocol and path are appended correctly for different filesystems
        save_path = get_filepath_str(self._get_save_path(), self._protocol)
        NUM_ROWS_IN_INPUT = 1
        NUM_FEATURES_IN_INPUT = 14

        with self._fs.open(save_path, "wb") as f:            
            initial_type = [('float_input', FloatTensorType((NUM_ROWS_IN_INPUT, NUM_FEATURES_IN_INPUT)))]
            options = {id(data): {'zipmap': False}} # enables getting probabilities in Node.
            onx = convert_sklearn(data, initial_types=initial_type, options=options)
            f.write(onx.SerializeToString())

    def _describe(self) -> Dict[str, Any]:
        return dict(
            filepath=self._filepath, version=self._version, protocol=self._protocol
        )
