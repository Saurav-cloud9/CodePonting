import kagglehub
import shutil

#path1 = kagglehub.dataset_download("debashis74017/stock-market-data-nifty-50-stocks-1-min-data")
#shutil.copytree(path1, r"C:\Users\Saurav\CodePonting\Algo_Trading\kaggle\dataset1")
#print("Dataset 1 saved.")

#path2 = kagglehub.dataset_download("debashis74017/algo-trading-data-nifty-100-data-with-indicators")
#shutil.copytree(path2, r"C:\Users\Saurav\CodePonting\Algo_Trading\kaggle\dataset2")
#print("Dataset 2 saved.")

# dataset2 folder already exists from partial copy.
# Fix: add dirs_exist_ok=True to copytree

path2 = kagglehub.dataset_download("debashis74017/algo-trading-data-nifty-100-data-with-indicators")
shutil.copytree(path2, r"C:\Users\Saurav\CodePonting\Algo_Trading\kaggle\dataset2", dirs_exist_ok=True)
print("Dataset 2 saved.")