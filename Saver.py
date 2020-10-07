import pandas as pd
import os


def save_data(path, newData):
    """
    :param path: path+file name
    :param newData: new data as [[time,ppm],[time,ppm]]
    :return: none
    """
    header = ["time", "ppm"]
    if path == "":
        path = "G:"
    path = path + r"\data.xlsx"
    if not os.path.exists(path):
        df = pd.DataFrame(columns=header)
        df.to_excel(path, index=False)
    else:
        df = pd.read_excel(path)
    newDf = pd.DataFrame(newData, columns=header)
    df = df.append(newDf, ignore_index=False)
    df.to_excel(path, index=False)
    print("excel write successfully")

# if __name__ == '__main__':
#     fileName = "co2.xlsx"
#     path = "G:\\WXB\\Datas\\"
#     print(os.path.exists(path + fileName))
#     save_data("G:\\WXB\\Datas\\test.xlsx", [["asd", 46554], ["afag", 464]])
