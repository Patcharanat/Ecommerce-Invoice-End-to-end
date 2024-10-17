import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler
from sklearn.cluster import KMeans

from abstract import AbstractMLService, AbstractMLProcessor


class BaseMLService(AbstractMLService):
    def __init__(self):
        super().__init__()

    def etc_method():
        pass

class CustomerProfilingProcessor(BaseMLService):
    """RFM"""
    def __init__(
        self, 
        input_df: pd.DataFrame
    ):
        super().__init__()
        self.input_df = input_df
        self.sample_df = input_df.copy()
        self.unique_invoice: pd.DataFrame | None = None
        self.customer_profile: pd.DataFrame | None = None
    
    def drop_anonymous(self, sample_df: pd.DataFrame) -> pd.DataFrame:
        """Drop CustomerID = '0' from sample DataFrame"""
        anonymous_customer_index = sample_df[sample_df['CustomerID'] == 0].index
        sample_df = sample_df.drop(index=anonymous_customer_index)
        return sample_df

    def distinct_customer_invoice(self, sample_df: pd.DataFrame | None) -> pd.DataFrame:
        """Create/update class attribute of unique_invoice with unique customer-invoice DataFrame for re-usage"""
        if self.unique_invoice is not None:
            return self.unique_invoice.copy()
        else:
            unique_invoice = sample_df[['CustomerID', 'InvoiceNo', 'InvoiceDate']].drop_duplicates(['InvoiceNo'])
            self.unique_invoice = unique_invoice
            return self.unique_invoice.copy()

    def get_recency(self, sample_df: pd.DataFrame | None = None) -> pd.DataFrame:
        """Create Recency DataFrame for RFM framework"""
        unique_invoice = self.distinct_customer_invoice(sample_df=sample_df)
        
        unique_invoice['recency'] = unique_invoice.groupby('CustomerID')['InvoiceDate'].diff().dt.days
        recency_df = unique_invoice.drop_duplicates("CustomerID", keep='last')

        # null value occured in recency for first time buyer
        calculation_date = unique_invoice["InvoiceDate"].max()
        recency_df['recency'] = recency_df["recency"].fillna((calculation_date - unique_invoice["InvoiceDate"])) \
                                                    .apply(lambda x: x if type(x) == float else x.days) \
                                                    .astype(int)
        recency_df = recency_df.drop(columns=['InvoiceNo', 'InvoiceDate'])

        return recency_df

    def get_frequency(self, sample_df: pd.DataFrame) -> pd.DataFrame:
        """Create Frequency DataFrame for RFM framework"""
        freq_df = sample_df.groupby(['CustomerID'])['InvoiceNo'].nunique().reset_index().rename({'InvoiceNo': 'frequency'}, axis=1)
        return freq_df

    def get_monetary(self, sample_df: pd.DataFrame) -> pd.DataFrame:
        """Create Monetary DataFrame for RFM framework"""
        monetary_df = sample_df.groupby('CustomerID')["total_spend"].sum().reset_index().rename({'total_spend': 'monetary'}, axis=1)
        return monetary_df

    def process_rfm(self, rfm_dfs: list[pd.DataFrame]) -> pd.DataFrame:
        """Merge all rfm properties into a DataFrame as customer_profile DataFrame"""
        customer_profile = rfm_dfs[0].merge(rfm_dfs[1], on='CustomerID').merge(rfm_dfs[2], on='CustomerID')
        self.customer_profile = customer_profile
        return customer_profile

    def feature_en_additional(
            self, 
            customer_profile: pd.DataFrame,
            sample_df: pd.DataFrame
        ) -> pd.DataFrame:
        """
        Execute Feature Engineering for a better customer behavior segmentation
        1. is_first_time_buyer
        2. mean time between purchases
        3. mean ticket_size (AVG spent per transaction) + mean_qty + mean_unique_item
        4. mean spent per month + freq per month

        And then post-processing with merging to customer_profile (input RFM) returning a DataFrame
        as 'enriched_customer_profile'
        """
        # 1. is_first_time_buyer
        customer_profile.loc[customer_profile['recency'].isnull(), 'is_first_time_buyer'] = int(1)
        customer_profile['is_first_time_buyer'] = customer_profile['is_first_time_buyer'].fillna(0).astype(int)
        
        # 2. mean time between purchases
        # prep recency
        unique_invoice: pd.DataFrame = self.distinct_customer_invoice()
        unique_invoice['recency'] = unique_invoice.groupby('CustomerID')['InvoiceDate'].diff().dt.days
        # calculate mean recency
        mean_time_interval = unique_invoice.groupby('CustomerID').agg({"recency": lambda x: x.diff().abs().mean()})\
                                            .reset_index()\
                                            .sort_values("CustomerID")
        mean_time_interval = mean_time_interval.rename(columns={'recency': 'mean_time_interval'})
        mean_time_interval['mean_time_interval'] = mean_time_interval['mean_time_interval'].apply(lambda x: round(x, 2))
        # fill null for first time customer with calculated exact recency
        recency_customer_profile = customer_profile.sort_values("CustomerID")\
                                                    .reset_index(drop=True)
        mean_time_interval = mean_time_interval.combine_first(
            recency_customer_profile.sort_values("CustomerID")\
                                    .rename(columns={"recency": "mean_time_interval"})\
                                    .reset_index(drop=True)
        )
        
        # 3. mean ticket_size (AVG spent per transaction) + mean_qty + mean_unique_item
        mean_per_purchase = sample_df.groupby(['CustomerID', 'InvoiceNo'])\
                                    .agg({
                                        "total_spend": "sum", # aggregate some for each InvoiceNo and CustomerID
                                        "Quantity": "sum",
                                        "StockCode": "nunique"
                                    })\
                                    .groupby('CustomerID')\
                                    .agg({
                                        "total_spend": "mean", # aggregate mean for each CustomerID
                                        "Quantity": "mean",
                                        "StockCode": "mean"
                                    })\
                                    .reset_index()\
                                    .rename(columns={
                                        'total_spend': 'mean_ticket_size',
                                        "Quantity": "mean_quantity",
                                        "StockCode": "mean_unique_item"
                                    })\
                                    .round(2)
        
        # 4. mean spent per month + freq per month
        per_period = sample_df[['CustomerID', 'InvoiceNo', 'StockCode', 'InvoiceDate', 'total_spend']].copy()
        per_period['month'] = per_period['InvoiceDate'].dt.month

        per_month = per_period.groupby(['CustomerID', 'month'])\
                                .agg({"InvoiceNo": "nunique", "total_spend": "mean"})\
                                .groupby(['CustomerID'])\
                                .agg({"InvoiceNo": "mean", "total_spend": "mean"})\
                                .round(2)\
                                .reset_index()\
                                .rename(columns={'InvoiceNo': 'freq_per_month', 'total_spend': 'mean_spent_per_month'})

        # post-process: aggregate engineered features to customer_profile
        enriched_customer_profile = customer_profile.merge(mean_time_interval, on='CustomerID')\
                                                    .merge(mean_per_purchase, on='CustomerID')\
                                                    .merge(per_month, on='CustomerID')
        return enriched_customer_profile

    def preprocess(self) -> pd.DataFrame:
        """Entrypoint for data preprocessing"""
        df = self.drop_anonymous(sample_df=self.sample_df)
        recency_df = self.get_recency(sample_df=df)
        frequency_df = self.get_frequency(sample_df=df)
        monetary_df = self.get_monetary(sample_df=df)
        customer_profile = self.process_rfm(rfm_dfs=[recency_df, frequency_df, monetary_df])
        enriched_customer_profile = self.feature_en_additional(
            customer_profile=customer_profile,
            sample_df=df
        )
        return enriched_customer_profile


class CustomerSegmentationProcessor(BaseMLService):
    """Kmeans"""
    def __init__(
        self,
        df: pd.DataFrame
    ):
        super().__init__()
        self.df = df
        self.scaler: RobustScaler | None

    def scale(self, df: pd.DataFrame) -> tuple[pd.DataFrame, RobustScaler]:
        """
        Scale DataFrame with RobustScaler\n
        Input: enriched_customer_profile (rfm + engineered features)\n
        Output: scaled enriched_customer_profile for being KMeans input

        :param df: enriched_customer_profile (or customer_profile/rfm)
        :type df: pd.DataFrame
        """
        scaler = RobustScaler()
        scaled_df = scaler.fit_transform(df.drop(columns=["CustomerID"]))
        
        # save output
        self.scaler = scaler
        scaled_df = pd.DataFrame(scaled_df, columns=df.drop(columns=["CustomerID"]).columns)

        return scaled_df, scaler

    def train(self, df: pd.DataFrame) -> tuple[list, KMeans]:
        """create distortions for the dataset with the scaled customer_profile"""
        # prepare variables for looping
        feature_number = len(df.columns)
        distortions = []

        for k in range(1, feature_number+1):
            kmeans = KMeans(
                n_clusters=k,
                init="k-means++",
                n_init="auto",
                random_state=0
            )
            kmeans.fit(df)
            distortions.append(kmeans.inertia_)
        
        return distortions

    def find_best_elbow(distortions: list) -> int:
        """
        Function to find the optimal k considered by distortions
        """
        array_distortions = np.array(distortions)
        # 1st derivative: graph slope
        slopes = np.divide(array_distortions[1:], array_distortions[:-1])
        # 2nd derivative: rate of change
        slope_changes = np.diff(slopes)

        # tmp variables used in slope calculation in the next process
        tmp_slopes = slopes.copy()
        tmp_slope_changes = slope_changes.copy()

        # find the most optimal k
        while True:
            try:
                # find the lowest slope change (the most linear index)
                min_slope_change_index = np.argmin(abs(tmp_slope_changes))

                # verifying if there's no lower slope after the most linear point
                if (tmp_slope_changes[min_slope_change_index] < tmp_slopes[min_slope_change_index:]).all():
                    k_optimal = min_slope_change_index + 2
                else:
                    tmp_slope_changes[min_slope_change_index] = 1
                    continue
                return k_optimal
            except Exception as e:
                raise ValueError(e)
    
    def clustering(
        self, 
        df: pd.DataFrame, 
        scaled_df: pd.DataFrame, 
        optimal_k: int
    ) -> pd.DataFrame:
        """
        Cluster inference,
        use 'scaled_df' as kmeans input and put the output into 'df' as a 'cluster' column name
        """
        kmeans = KMeans(
            n_clusters=optimal_k,
            init="k-means++",
            n_init="auto",
            random_state=0
        )
        output_df = df.copy()
        output_df["cluster"] = kmeans.fit(scaled_df).labels_

        return output_df, kmeans
    
    def process(self) -> tuple[pd.DataFrame, KMeans, RobustScaler]:
        """Entrypoint to orchestrate the processes"""
        scaled_df, scaler = self.scale(df=self.df)
        
        distortions = self.train(df=scaled_df)
        optimal_k = self.find_best_elbow(distortions=distortions)
        
        output_df, trained_kmeans = self.clustering(
            df=self.df,
            scaled_df=scaled_df,
            optimal_k=optimal_k
        )

        return output_df, trained_kmeans, scaler


class ClusterInterpretationProcessor(BaseMLService):
    """LightGBM"""
    pass


class MlProcessor(AbstractMLProcessor):
    pass
