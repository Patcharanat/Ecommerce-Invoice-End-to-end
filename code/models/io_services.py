import os
from typing import Any
from pathlib import Path
import logging
import json
from datetime import datetime

import pandas as pd
import duckdb
import pickle

from abstract import AbstractIOReaderWriter, AbstractInputReader, AbstractOutputWriter, AbstractIOProcessor


class BaseIOReaderWriter(AbstractIOReaderWriter):
    def __init__(self):
        pass

    @property
    def __str__(self):
        bases = [base.__name__ for base in self.__class__.__bases__]
        bases.append(self.__class__.__name__)
        return ".".join(bases)

    @staticmethod
    def list_model_in_path(
        model_path: str | Path, 
        model_name: str = None
    ) -> list[str]:
        """
        List models in the specified folder
        """
        files = os.listdir(model_path)
        
        if model_name is not None:
            model_files = [file for file in files if model_name in file]
        else:
            model_files = files
        
        return model_files

    def find_latest_model(
        self, 
        model_path: str | Path, 
        model_name: str
    ) -> Path | None:
        """
        Find the latest model version path with specified model name
        """
        model_files = self.list_model_in_path(
            model_path=model_path,
            model_name=model_name
        )

        if len(model_files) != 0:
            # retrieve the latest model version as a name
            latest_model = Path(max(model_files))
            
            return latest_model
        else:
            return None


class BaseInputReader(AbstractInputReader, BaseIOReaderWriter):
    def __init__(self):
        super().__init__()

    @staticmethod
    def is_db_exists(input_path: str) -> bool:
        # os.path.isfile(path=input_path) -> bool
        data_file = Path(input_path)
        return data_file.is_file()

    @staticmethod
    def connect_db(input_path: str) -> tuple:
        con = duckdb.connect(input_path)
        cursor = con.cursor()
        return (cursor, con)

    @staticmethod
    def render_sql(file_path: str) -> str:
        with open(file_path, "r") as sql_f:
            statement = sql_f.read()
        sql_f.close()
        return statement


class BaseOutputWriter(AbstractOutputWriter, BaseIOReaderWriter):
    def __init__(self):
        super().__init__()


class BaseIOProcessor(AbstractIOProcessor):
    def __init__(self):
        super().__init__()

    @property
    def __str__(self):
        bases = [base.__name__ for base in self.__class__.__bases__]
        bases.append(self.__class__.__name__)
        return ".".join(bases)


class LocalInputReader(BaseInputReader):
    """
    :param method: *(Required)* Source type to read from.\n
        Parameters choices: ['db', 'filesystem']
    :type method: str

    :param input_path: *(Required)* Path to a source file or a local db file
    :type input_path: str

    :param init_script_path: *(Optional)* Path to initial script for database initialization
    :type init_script_path: str

    :param init_data_path: *(Optional)* Path to initial data path for database initialization
    :type init_data_path: str
    """

    def __init__(
        self,
        method: str,
        input_path: str,
        output_path: str,
        init_script_path: str = "db/sql/init_sales.sql",
        init_data_path: str = "../../data/ecomm_invoice_transaction.parquet",
    ):
        super().__init__()
        self.method = method
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        # sql_path
        # data_model
        self.init_script_path = init_script_path
        self.init_data_path = init_data_path

        if method == "db":
            if self.is_db_exists(input_path):
                logging.info("Input database exists, no initialization required")
            else:
                logging.info("Input database not exists, method 'db', initializing db...")
                self.init_db()
        elif method == "filesystem":
            logging.warning(
                "method 'filesystem', no initialization required"
            )
        else:
            raise Exception(
                "Database is not exist. Unacceptable `method` argument for Reader."
            )

    def init_db(self) -> None:
        # connect local db
        cursor, con = self.connect_db(path=self.input_path)

        # read initial script
        statement = self.render_sql(self.init_script_path)
        # execute sql
        sql_params = {
            "data_model": "ecomm_gold.sales_transaction",  # only sales data is acceptable for initialization
            "data_path": self.init_data_path,
        }
        cursor.execute(statement, parameters=sql_params)
        # .execute() return connection
        # .sql() return relation (table)
        con.close()

    def read_data(self, input_path: Path):
        logging.info(f"Reading data file: {input_path.name}")
        # Path().stem, Path().suffix, Path().name, Path().parent
        
        df = pd.read_parquet(input_path)
        
        logging.info(f"Successfully read data file: {input_path.name}")

        return df

    def is_model_exist(
            self, 
            model_path: str | Path,
            model_name: str = None
        ) -> bool:
        """
        Check if interpreter is available

        Return
        ------
        - is_model_exist flag
        - path to model if exists with latest version (None if no model exists)
        """
        
        model_files = self.list_model_in_path(
            model_path=model_path, 
            model_name=model_name
        )

        if len(model_files) != 0:
            return True
        else:
            return False
    
    def read_interpreter(self, output_path: Path) -> Any:
        """
        Read interpreter model with pickle

        Return
        ------
        Model: Any
        """

        logging.info(f"Searching for Interpreter Model from: {output_path}")

        model_path = output_path / "models"

        # create folder if not exist
        model_path.mkdir(parents=True, exist_ok=True)

        if self.is_model_exist(model_path=model_path, model_name="interpreter"):
            logging.info("Interpreter is available, Read Interpreter...")

            # find latest version
            latest_mdoel = self.find_latest_model(
                model_path=model_path,
                model_name="interpreter"
            )
            logging.info(f"Found the latest model as: {latest_mdoel}")

            # read model with pickle
            with open(model_path / latest_mdoel, "rb") as f:
                interpreter = pickle.load(f)
                f.close()
            logging.info("Successfully Read Interpreter")
        else:
            logging.info("Interpreter is not available, Skipped")

            interpreter = None
        
        return interpreter

    def read(self, sql_path: str = None, sql_params: dict = None) -> pd.DataFrame:
        if self.method == "db":
            # logging.info(f"Reading db path from: {self.input_path}")

            # # connect db
            # cursor, con = self.connect_db(path=sql_path)

            # # execute reading input statement, then load to pandas dataframe
            # statement = self.render_sql(sql_path)
            # df = cursor.sql(statement, parameters=sql_params).to_df()

            # con.close()
            # return df
            raise ValueError("Method 'db' is not implemented yet.")

        elif self.method == "filesystem":
            logging.info(f"Reading filesystem path from: {self.input_path}")

            # reading data
            df = self.read_data(input_path=self.input_path)

            # interpreter
            interpreter = self.read_interpreter(output_path=self.output_path)

            # formulate input for model services
            inputs: dict = {
                "df": df,
                "interpreter": interpreter
            }

            return inputs

        else:
            raise Exception("Unacceptable `method` argument for Reader.")


class GCPInputReader(BaseInputReader):
    pass


class DockerDatabaseInputReader(BaseInputReader):
    pass


class InputProcessor(BaseIOProcessor):
    """
    Entrypoint for InputReader instance, selecting connection/environment type by given parameters.
    """

    def __init__(
        self,
        env: str,
        method: str,
        input_path: str = None,
        output_path: str = None
    ):
        self.env = env
        self.method = method
        self.input_path = input_path
        self.output_path = output_path
        self.factory = {
            "local": LocalInputReader,
            "postgresql": DockerDatabaseInputReader,
            "gcp": GCPInputReader,
        }

    def process(self):
        logging.info(f"Processor: {self.__str__}")

        reader_instance = self.factory.get(self.env)
        reader_args = {
            "method": self.method,
            "input_path": self.input_path,
            "output_path": self.output_path
        }
        reader = reader_instance(**reader_args)
        
        logging.info(f"Selected reader: {reader.__str__}")
        logging.info(f"Reader arguments: {reader_args}")

        if reader_instance:
            return reader.read()
        else:
            raise Exception("No InputReader assigned in InputProcessor factory")


class LocalOutputWriter(BaseOutputWriter):
    def __init__(
        self,
        method: str,
        output_path: str,
        date: str,
        output: dict,
    ) -> None:
        super().__init__()
        self.method = method
        self.output_path = Path(output_path)
        self.date = date
        self.output = output

    def build_control_file_dict(self, artifacts: dict[str, Any]) -> dict:
        control_file_dict: dict = {}
        control_file_dict["interpreter_params"] = artifacts.get("interpreter_params")
        control_file_dict["interpreter_metrics"] = artifacts.get("interpreter_metrics")
        control_file_dict["is_train_interpreter"] = artifacts.get("is_train_interpreter")
        control_file_dict["is_anomaly_exist"] = artifacts.get("is_anomaly_exist")

        return control_file_dict

    def find_latest_model_version(
        self,
        model_path: str | Path,
        model_name: str
    ) -> int:
        latest_model = self.find_latest_model(
            model_path=model_path, 
            model_name=model_name
        )
        latest_version = Path(latest_model).name.split("_v")[-1]

        return latest_version

    def write_element(
        self, 
        output: Any, 
        element_type: str, 
        filename: str
    ) -> None:
        """
        Writing output file depends on arguments

        Parameters
        ----------
        - output: pd.DataFrame | KMeans | LGBMClassifier | dict
        - element_type: str
        - filename: str
        """
        if element_type == "data":
            # prep filename and path
            data_file_name = f"{str(filename)}.parquet"
            # date = datetime.today().date().strftime("%Y-%m-%d")
            data_path = self.output_path / "data" / self.date

            # create directory if not exist
            data_path.mkdir(parents=True, exist_ok=True)

            # export
            output.to_parquet(data_path / data_file_name)
            
            # logs
            logging.info(f"Successfully export data to {str(data_path)} output as {data_file_name}")
        
        elif element_type == "model":
            # prep path
            model_path = self.output_path / "models"

            # create directory if not exist
            model_path.mkdir(parents=True, exist_ok=True)
            
            # dynamic bump model version if available
            files = os.listdir(model_path)
            model_files = [file for file in files if file.startswith(filename)]

            if len(model_files) != 0:
                version = int(Path(max(model_files)).stem.split("_v")[1]) + 1
            else:
                version = 1
            
            # prep filename and path
            model_file_name = f"{filename}_v{version}.pkl"
            model_path = model_path / model_file_name

            # export
            with open(model_path, "+wb") as f:
                pickle.dump(output, f)
                f.close()

            # logs
            logging.info(f"Successfully export model to {str(model_path)} output as {model_file_name}")

        elif element_type == "artifact":
            # aka control file as json
            # prep filename and path
            artifact_file_name = f"{filename}.json"
            artifact_path = self.output_path / "artifact" / self.date

            # create directory if not exist
            artifact_path.mkdir(parents=True, exist_ok=True)

            # export
            with open(artifact_path / artifact_file_name, "+w") as f:
                json.dump(output, f, indent=4)
                f.close()

            # logs
            logging.info(f"Successfully export control file (artifact) to {str(artifact_path)} as {artifact_file_name}")

    def write(self, sql_path: str = None, sql_params: dict = None) -> None:
        if self.method == "db":
            # connect db
            cursor, con = self.connect_db(path=self.output_path)

            # reading sql file rendering sql statement
            statement = self.render_sql(file_path=sql_path)

            # execute writing output statement to load pandas DataFrame to duckdb database
            # https://duckdb.org/docs/guides/python/import_pandas.html
            in_memory_df = self.df
            in_memory_df_param = "in_memory_df"
            sql_params = {**sql_params, in_memory_df_param: in_memory_df}
            cursor.sql(statement, parameters=sql_params)

            con.close()
            logging.info(
                f"Successfully write output file: {Path(self.output_path).name}"
            )
            return 1

        elif self.method == "filesystem":
            # writing file
            logging.info(f"Writing file to: {Path(self.output_path)}")
            
            # data model
            logging.info("Exporting... Data Models")
            df_cluster_rfm: pd.DataFrame = self.output.get("df_cluster_rfm")
            df_cluster_importance: pd.DataFrame = self.output.get("df_cluster_importance")

            self.write_element(output=df_cluster_rfm, element_type="data", filename="df_cluster_rfm")
            self.write_element(output=df_cluster_importance, element_type="data", filename="df_cluster_importance")

            # ml model
            logging.info("Exporting... ML Models")
            segmenter_trained = self.output.get("segmenter_trained")
            segmenter_scaler = self.output.get("segmenter_scaler")
            interpreter = self.output.get("interpreter")

            self.write_element(output=segmenter_trained, element_type="model", filename="kmeans_segmenter")
            self.write_element(output=segmenter_scaler, element_type="model", filename="segmenter_scaler")
            self.write_element(output=interpreter, element_type="model", filename="lgbm_interpreter")


            # other artifacts
            logging.info("Exporting... Artifact (Control file)")

            interpreter_params = self.output.get("interpreter_params")
            interpreter_metrics = self.output.get("interpreter_metrics")
            is_train_interpreter = self.output.get("is_train_interpreter") # boolean
            # latest_model_version = self.find_latest_model_version(model_path=) #TODO: solve this logic finding the latest trained model version
            is_anomaly_exist = self.output.get("is_anomaly_exist") # boolean

            # aggregate artifact
            artifacts = {
                "interpreter_params": interpreter_params,
                "interpreter_metrics": interpreter_metrics,
                "is_train_interpreter": is_train_interpreter,
                # "latest_trained_model_version": latest_model_version,
                "is_anomaly_exist": is_anomaly_exist
            }
            control_file_dict =  self.build_control_file_dict(artifacts=artifacts)

            self.write_element(output=control_file_dict, element_type="artifact", filename="control_file")

        else:
            raise Exception("Unacceptable `method` argument for Reader.")


class GCPOutputWriter(BaseOutputWriter):
    pass


class DockerDatabaseOutputWriter(BaseOutputWriter):
    pass


class OutputProcessor(BaseIOProcessor):
    def __init__(
        self, 
        env: str, 
        method: str, 
        output_path: str,
        date: str,
        outputs: dict
    ):
        self.env = env
        self.method = method
        self.output_path = output_path
        self.date = date
        self.outputs = outputs
        self.factory = {
            "local": LocalOutputWriter,
            "postgresql": DockerDatabaseOutputWriter,
            "gcp": GCPOutputWriter,
        }

    def log_writer_args(self, writer_args: dict[str, Any]) -> None:
        """
        Exclude DataFrame element from output dict for cleaned logging
        """
        output_dict: dict = writer_args.get("output")
        
        output_dict_output: dict = {}
        output_dict_output["df_cluster_rfm"] = True if output_dict.get("df_cluster_rfm") is not None else False
        output_dict_output["df_cluster_importance"] = True if output_dict.get("df_cluster_importance") is not None else False
        output_dict_output["segmenter_trained"] = True if output_dict.get("segmenter_trained") is not None else False
        output_dict_output["segmenter_scaler"] = True if output_dict.get("segmenter_scaler") is not None else False
        output_dict_output["interpreter"] = True if output_dict.get("interpreter") is not None else False
        output_dict_output["interpreter_params"] = output_dict.get("interpreter_params")
        output_dict_output["interpreter_metrics"] = output_dict.get("interpreter_metrics")
        output_dict_output["is_train_interpreter"] = output_dict.get("is_train_interpreter")
        output_dict_output["is_anomaly_exist"] = output_dict.get("is_anomaly_exist")
        
        output_log = {**writer_args}
        output_log["output"] = output_dict_output

        # pretty logs
        logging.info(f"Writer arguments: {output_log}")

    def process(self) -> None:
        logging.info(f"Processor: {self.__str__}")

        writer_instance = self.factory.get(self.env)
        writer_args = {
            "method": self.method,
            "output_path": self.output_path,
            "date": self.date,
            "output": self.outputs
        }
        writer = writer_instance(**writer_args)

        logging.info(f"Selected writer: {writer.__str__}")
        self.log_writer_args(writer_args)

        if writer_instance:
            return writer.write()
        else:
            raise Exception("No OutputWriter assigned in OutputProcessor factory")
