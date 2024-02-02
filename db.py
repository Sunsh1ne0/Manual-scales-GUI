import sqlite3
import datetime
import math
import zipfile
import io
from io import StringIO
import os
import shutil


def create_blank_db(dest_dir, filename):
    try:
        shutil.copyfile("blank.b1d", dest_dir + filename)
    except Exception:
        print(f'Failed to copy to database from "/home/ubuntu/agrobit-b-backend/src/chicken_sorter_main_node/blank.b1d" to {filename}')


def add_file_table(dest_dir, filename, count):
    os.chdir(dest_dir)
    try:
        db = sqlite3.connect(filename, check_same_thread=False)
        cur = db.cursor()
    except Exception:
        print(f'Failed to connect to database {filename}')
    try:
        exec_str = """
            INSERT INTO Files
            (FileId, ScaleConfigId, Name, Note, EnableMoreBirds, NumberOfBirds, WeightSortingMode, LowLimit, HighLimit, SavingMode, "Filter", StabilizationTime, StabilizationRange, MinimumWeight)
            VALUES(1, 1, 'AGROBIT', '', 0, {}, 0, 1.0, 2.0, 2, 1.0, 0.5, 1.0, 0.1);
        """.format(count)
        cur.execute(exec_str)
        db.commit()
    except Exception:
        print(f'Failed to commit in database {filename} during adding file table')


def add_samples_table(dest_dir, filename, id, weight, flag, time_now):
    os.chdir(dest_dir)
    try:
        db = sqlite3.connect(filename, check_same_thread=False)
        cur = db.cursor()
    except Exception:
        print(f'Failed to connect in database {filename}')
    try:
        # time_now = get_julian_datetime(datetime.datetime.now())
        exec_str = """
            INSERT INTO Samples
            (WeighingId, Weight, Flag, SavedDateTime)
            VALUES(1, {}, {}, {});
        """.format(weight, flag, time_now)
        cur.execute(exec_str)
        db.commit()
    except Exception:
        print(f'Failed to commit in database {filename} during adding samples table')

def add_weightings_table(dest_dir, filename):
    os.chdir(dest_dir)
    try:
        db = sqlite3.connect(filename, check_same_thread=False)
        cur = db.cursor()
    except Exception:
        print(f'Failed to connect in database {filename}')
    try:
        time_now = get_julian_datetime(datetime.datetime.now())
        exec_str = """
            INSERT INTO Weighings
            (WeighingId, FileId, ScaleConfigId, ResultType, RecordSource, DownloadedDateTime, Note, SwMajorVersion, SwMinorVersion, SwBuildVersion, SamplesMinDateTime, SamplesMaxDateTime)
            VALUES(1, 1, 1, 0, 0, {}, '', 8, 0, 709, {}, {});
        """.format(time_now, time_now, time_now)
        cur.execute(exec_str)
        db.commit()
    except Exception:
        print(f'Failed to commit in database {filename} during adding weightings table')

def save_db_in_file(dest_dir, filename):
    os.chdir(dest_dir)
    info = "{}\n8.0.5.709\nWEIGHINGS".format(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
    try:
        os.remove(filename + ".b1e")
    except Exception:
        pass
    try:
        with zipfile.ZipFile(filename + ".b1e", 'w') as myzip:
            myzip.write(filename + ".b1d")
            myzip.writestr('Info.txt', info)
            # os.sync()
    except Exception:
        print(f'Failed to save database {filename + ".b1d"} in ".b1e"')
        return 

def get_julian_datetime(date):
    """
    Convert a datetime object into julian float.
    Args:
        date: datetime-object of date in question

    Returns: float - Julian calculated datetime.
    Raises:
        TypeError : Incorrect parameter type
        ValueError: Date out of range of equation
    """
    # Ensure correct format
    if not isinstance(date, datetime.datetime):
        raise TypeError('Invalid type for parameter "date" - expecting datetime')
    # Perform the calculation
    julian_datetime = (367 * date.year - int((7 * (date.year + int((date.month + 9) / 12.0))) / 4.0) 
                       + int((275 * date.month) / 9.0) + date.day + 1721013.5 
                       + (date.hour + date.minute / 60.0 + date.second / math.pow(60,2)) / 24.0 
                       - 0.5 * math.copysign(1, 100 * date.year + date.month - 190002.5) + 0.5)
    return julian_datetime