import numpy as np
import pandas as pd
#Simport dvc.api
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, GridSearchCV, KFold, RandomizedSearchCV, cross_val_score
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve, confusion_matrix, accuracy_score, precision_recall_curve, f1_score, mean_squared_error, r2_score, mean_absolute_error, auc
from sklearn.tree import DecisionTreeClassifier, plot_tree
#from xgboost import plot_tree, XGBClassifier, DMatrix
#from scipy.stats import uniform


def import_all_data_using_tagslist(path: str, repo: str, tags: list) -> dict:
    df_dict = {}
    for each in tags:
        data_url = dvc.api.get_url(path=path, repo=repo, rev=each)
        df_dict[each] = pd.read_csv(data_url)

    return df_dict

# Selecting only browsers with more than 100 rows or users


def get_index_based_on_size(size: np.array, value: int) -> list:
    size = size.tolist()
    index_list = []
    for index in range(len(size)):
        if(size[index] >= value):
            index_list.append(index)

    return index_list


def get_df_of_each_group(grouped_df: pd.DataFrame, selected_index: list) -> list:
    size_series = grouped_df.size()
    df_list = []
    for index in selected_index:
        df = grouped_df.get_group(size_series.index[index])
        df_list.append(df.reset_index().drop('index', axis=1))

    return df_list


def split_date_to_numbers(df_dict: dict, date_column: str) -> dict:
    new_dict = df_dict.copy()
    for df in new_dict:
        new_dict[df][date_column] = pd.to_datetime(new_dict[df][date_column])
        new_dict[df]['year'] = new_dict[df][date_column].apply(
            lambda x: x.date().year)
        new_dict[df]['month'] = new_dict[df][date_column].apply(
            lambda x: x.date().month)
        new_dict[df]['day'] = new_dict[df][date_column].apply(
            lambda x: x.date().day)
        new_dict[df] = new_dict[df].drop(date_column, axis=1)

    return new_dict


def change_columns_to_numbers(df_dict: dict, columns: list) -> dict:
    lb = LabelEncoder()
    new_dict = df_dict.copy()
    for df in new_dict:
        df_columns = new_dict[df].columns.to_list()
        for change_col in columns:
            if(change_col in df_columns):
                new_dict[df][change_col] = lb.fit_transform(
                    new_dict[df][change_col])

    return new_dict


def get_train_validate_test_sets(df: pd.DataFrame, predicted_column: str, remove_columns: list, train_perc: float = 0.7, val_perc: float = 0.2, test_perc: float = 0.1) -> dict:
    data_dict = {}
    if(train_perc * 10 + val_perc * 10 + test_perc * 10 == 10):
        r_size = df.shape[0]
        train_columns = df.columns.to_list()
        train_columns.remove(predicted_column)

        for column in remove_columns:
            try:
                train_columns.remove(column)
            except:
                pass

        train_part = df.iloc[:int(r_size * (train_perc + val_perc)), :]
        test_part = df.iloc[int(r_size * (train_perc + val_perc)):, :]

        train_x, val_x, train_y, val_y = train_test_split(train_part.loc[:, train_columns],
                                                          train_part[predicted_column], test_size=val_perc)

        data_dict['train_x'] = train_x
        data_dict['train_y'] = train_y
        data_dict['val_x'] = val_x
        data_dict['val_y'] = val_y
        data_dict['test_x'] = test_part.loc[:, train_columns]
        data_dict['test_y'] = test_part.loc[:, predicted_column]

        return data_dict
    else:
        print("Invalid percentages used")
        return {}

# New additions


def calculate_metrics(y_test, y_preds):
    rmse = np.sqrt(mean_squared_error(y_test, y_preds))
    r_sq = r2_score(y_test, y_preds)
    mae = mean_absolute_error(y_test, y_preds)

    return {'RMSE Score': rmse, 'R2_Squared': r_sq, 'MAE Score': mae}


def evaluate_model(dt_classifier, x_valid, y_valid, x_test, y_test, show=False):
    valid_accuracy_score = accuracy_score(
        y_valid, dt_classifier.predict(x_valid))
    valid_confusion_value = confusion_matrix(
        y_valid, dt_classifier.predict(x_valid))

    test_accuracy_score = accuracy_score(
        y_test, dt_classifier.predict(x_test))
    test_confusion_value = confusion_matrix(
        y_test, dt_classifier.predict(x_test))

    if(show):
        print(f"Validation Accuracy : {valid_accuracy_score}")
        print("Validation Confusion Matrix:")
        print(valid_confusion_value)
        print("-"*50)
        print(f"Test Accuracy : {test_accuracy_score}")
        print("Test Confusion Matrix:")
        print(test_confusion_value)

    return (valid_accuracy_score, valid_confusion_value, test_accuracy_score, test_confusion_value)

# result plotters


def plot_preds(y_test, y_preds, model_name):
    N = len(y_test)
    original = plt.scatter(np.arange(1, N+1), y_test, c='blue')
    prediction = plt.scatter(np.arange(1, N+1), y_preds, c='red')
    plt.xticks(np.arange(1, N+1))
    plt.xlabel('# Oberservation')
    plt.ylabel('Response')
    title = 'True labels vs. Predicted Labels ({})'.format(model_name)
    plt.title(title)
    # plt.figure(figsize=(20, 8))
    plt.legend((original, prediction), ('Original', 'Prediction'))
    plt.show()


def plot_roc_curve_log(x_test, y_test, model, label, show=False):
    logit_roc_auc = roc_auc_score(y_test, model.predict(x_test))
    fpr, tpr, thresholds = roc_curve(y_test, model.predict_proba(x_test)[:, 1])
    plt.plot(fpr, tpr, label='{} (area = {:0.2f})'.format(label, logit_roc_auc))
    plt.plot([0, 1], [0, 1], 'r--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Receiver Operating Characteristic')
    plt.legend(loc="lower right")
    if(show):
        plt.show()

    return plt


def plot_precision_recall_curve(x_test, y_test, model, label, show=False):

    predicted = model.predict(x_test)
    probs = model.predict_proba(x_test)
    precision, recall, thresholds = precision_recall_curve(
        y_test, probs[:, 1])
    f1_score(y_test, predicted)
    auc_value = auc(recall, precision)
    plt.plot(recall, precision,
             label='{} (area = {:0.2f})'.format(label, auc_value))
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Precision')
    plt.ylabel('Recall')
    plt.title('Precision Recall Curve')
    plt.legend(loc="lower right")
    if(show):
        plt.show()

    return plt

# logistic regression plotter and trainer


def train_logistic_model(x_train, y_train, x_valid, y_valid, cross_val_size: int = 5):
    cv_acc_results = []
    model_list = []
    c = [0.001, 0.01, 0.1, 1, 10, 100, 1000]
    for i in c:
        # with mlflow.start_run():
        model = LogisticRegression(penalty='l2', C=i, multi_class='auto',
                                   solver='lbfgs', warm_start=True, random_state=42, n_jobs=-1)
        model.fit(x_train, y_train)
        kfold = KFold(n_splits=cross_val_size)
        results = cross_val_score(model, x_train, y_train, cv=kfold)
        # pre_acc_score = model.score(x_valid, y_valid)
        cv_scores = (results.mean(), results.std())
        cv_acc_results.append(cv_scores[0])
        model_list.append(model)


    best_model = model_list[cv_acc_results.index(min(cv_acc_results))]

    return best_model


# decision tree plotter and trainer


def get_dt_graph(dt_classifier, x, show=False):
    plt.figure(figsize=(25, 20))
    treeplt = plot_tree(dt_classifier,
                        feature_names=x.columns,
                        class_names=['No Response', "Yes Response"],
                        filled=True)
    if(show):
        plt.show()
    return plt


def train_decision_tree(x_train, y_train, x_valid, y_valid):
    dt = DecisionTreeClassifier(random_state=42)
    params = {
        'max_depth': [*range(3, 15)],
        'min_samples_split': [*range(2, 10)],
        'min_samples_leaf': [*range(1, 10)],
        'criterion': ["gini", "entropy"],
        'max_features': ['sqrt', 'log2'],
        # 'presort': [False, True],
        'class_weight': [None, 'balanced']
    }
    grid_search = GridSearchCV(estimator=dt,
                               param_grid=params,
                               cv=5, n_jobs=4, verbose=1, scoring="accuracy")
    grid_search.fit(x_train, y_train)


    return grid_search

# xgboost plotter and trainer


def get_xgbc_graph(model, x, rankdir=None, show=False):
    plt.figure(figsize=(20, 12))
    fig = plot_tree(model, fontsize=10, feature_names=x.columns,
                    filled=True, rankdir=rankdir)

    if(show):
        plt.show()

    return fig


def train_xgb_classifier(x_train, y_train, x_valid, y_valid):
    clf_xgb = XGBClassifier(use_label_encoder=False,
                            objective='binary:logistic')
    params = {
        'max_depth': [*range(3, 10)],
        'min_child_weight': [*range(1, 6)],
        'learning_rate': uniform(0.01, 0.59),
        'subsample': uniform(0.3, 0.6),
        'colsample_bytree': uniform(0.5, 0.4),
        # 'objective': "binary:logistic",
        # 'eval_metric': "logloss"
    }

    kfold = KFold(n_splits=5, shuffle=True)

    random_search = RandomizedSearchCV(clf_xgb, param_distributions=params,
                                       cv=kfold, n_iter=5, scoring='accuracy', error_score=0, verbose=1, n_jobs=4)

    random_search.fit(x_train, y_train)


    return random_search