import pandas as pd
import matplotlib.pyplot as plt


def plot_simple_dta(path=str, head2=str, converge=80, x=0.1, y=0.1, y_unit='', skiprows=2, mean=True):
    """
    Reads and plots simple .dta file.
    :param skiprows: Number of rows to be skipped
    :param path: Path to an .dta file
    :param head2: Name of y-axe
    :param converge: Percentage of the whole plot to define convergence
    :param x: Position of the convergence text within the plot
    :param y: Position of the convergence text within the plot
    :param y_unit: Unit of y-axe
    """
    head1 = 'Time'
    head_conv = 'Converge'
    c = (100 - converge)/100
    df = pd.read_csv(path, skiprows=skiprows, delimiter=' ', index_col=0, header=None)
    if mean:
        df.columns = [head2]
        df_conv = df.iloc[round(len(df)*c):]
        df_conv.columns = [head_conv]
        df_line = df.iloc[[0, -1]]
        mean = df_conv.mean().values[0]
        df_line.loc[0:] = mean
        plt.plot(df_conv, label=f'{converge}% of the initial plot to determine convergence')
        plt.plot(df_line, label=f'Convergence line')
    plt.subplots_adjust(right=0.98, top=0.95)
    plt.plot(df, label=f'{head2}')
    plt.ylabel(f'{head2}{y_unit}')
    plt.xlabel(f"{head1}, fs")
    plt.title(f'{head2} vs {head1}')
    plt.text(x, y, f'Converging to = {mean}', transform=plt.gca().transAxes)
    ax = plt.gca()
    # ax.xaxis.get_major_formatter().set_useOffset(False)
    # ax.xaxis.get_major_formatter().set_scientific(False)
    plt.legend()
    plt.rcParams["font.family"] = 'Times New Roman'
    plt.show()


if __name__ == '__main__':
    path_to_file = 'path/to/your/folder'
    y_ax_label2 = 'Coordination number'
    plot_simple_dta(path_to_file, y_ax_label, x=0.3, y=0.4, mean=False)
