import seaborn as sns
import matplotlib.pyplot as plt

def plot_correlation(returns):

    corr_matrix = returns.corr()

    plt.figure(figsize=(10,8))

    sns.heatmap(corr_matrix, annot=True, cmap="coolwarm")

    plt.title("Stock Correlation Heatmap")

    plt.savefig("../images/correlation_heatmap.png")

    plt.show()

    plt.show()