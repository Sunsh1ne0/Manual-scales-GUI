import sqlite3
import datetime
import math
import zipfile
import io
from io import StringIO
import os
import shutil


def create_blank_db(filepath):
    try:
        shutil.copyfile("blank.b1d", filepath)
    except Exception:
        print('Failed to copy to database from "/home/ubuntu/agrobit-b-backend/src/chicken_sorter_main_node/blank.b1d" to "%sExport.b1d"', filepath)


def add_file_table(dest_dir, count):
    #os.chdir(dest_dir)
    try:
        db = sqlite3.connect(dest_dir, check_same_thread=False)
        cur = db.cursor()
    except Exception:
        print('Failed to connect to database "%sExport.b1d"', dest_dir)
    try:
        exec_str = """
            INSERT INTO Files
            (FileId, ScaleConfigId, Name, Note, EnableMoreBirds, NumberOfBirds, WeightSortingMode, LowLimit, HighLimit, SavingMode, "Filter", StabilizationTime, StabilizationRange, MinimumWeight)
            VALUES(1, 1, 'AGROBIT', '', 0, {}, 0, 1.0, 2.0, 2, 1.0, 0.5, 1.0, 0.1);
        """.format(count)
        cur.execute(exec_str)
        db.commit()
    except Exception:
        print('Failed to commit in database "%sExport.b1d" during adding file table', dest_dir)


def add_samples_table(dest_dir, id, weight, flag, time):
    #os.chdir(dest_dir)
    try:
        db = sqlite3.connect(dest_dir, check_same_thread=False)
        cur = db.cursor()
    except Exception:
        print('Failed to connect in database "%sExport.b1d"', dest_dir)
    try:
        time_julian = get_julian_datetime(time)
        exec_str = """
            INSERT INTO Samples
            (WeighingId, Weight, Flag, SavedDateTime)
            VALUES(1, {}, {}, {});
        """.format(weight, flag, time_julian)
        cur.execute(exec_str)
        db.commit()
    except Exception:
        print('Failed to commit in database "%sExport.b1d" during adding samples table', dest_dir)


def delete_last_sample_table(dest_dir):
    os.chdir(dest_dir)
    try:
        db = sqlite3.connect('Export.b1d', check_same_thread=False)
        cur = db.cursor()
    except Exception:
        print('Failed to connect in database "%sExport.b1d"', dest_dir)
    try: 
        cur = db.cursor()
        exec_str = """
            delete from Samples where SavedDateTime = ( select max(SavedDateTime) from Samples );
        """
        cur.execute(exec_str)
        db.commit()
    except Exception:
        print('Failed to commit in database "%sExport.b1d" during deleting last sample from table', dest_dir)


def add_weightings_table(dest_dir):
    os.chdir(dest_dir)
    try:
        db = sqlite3.connect('Export.b1d', check_same_thread=False)
        cur = db.cursor()
    except Exception:
        print('Failed to connect in database "%sExport.b1d"', dest_dir)
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
        print('Failed to commit in database "%sExport.b1d" during adding weightings table', dest_dir)


def select_samples_table(dest_dir, flag):
    os.chdir(dest_dir)
    try:
        db = sqlite3.connect('Export.b1d', check_same_thread=False)
        cur = db.cursor()
    except Exception:
        print('Failed to connect in database "%sExport.b1d"', dest_dir)
    try:
        exec_str = """
            SELECT Weight 
            FROM Samples
            WHERE Flag = {}
            ORDER BY SavedDateTime DESC LIMIT 30000;
        """.format(flag)
        #ORDER BY WeighingId DESC_LIMIT 30000
        cur = db.cursor()
        cur.execute(exec_str)
        rows = cur.fetchall()
        return rows
    except Exception:
        print('Failed to commit in database "%sExport.b1d" during select samples from table', dest_dir)
        return 
    

def save_db_in_file(filepath, zip_filepath):
    dirname, filename = os.path.split(filepath)
    zip_dirname, zip_filename = os.path.split(zip_filepath)
    os.chdir(zip_dirname)
    info = "{}\n8.0.5.709\nWEIGHINGS".format(datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
    try:
        os.remove(zip_filename)
    except Exception:
        pass
    try:
        with zipfile.ZipFile(zip_filename, 'w') as myzip:
            myzip.write(filename)
            myzip.writestr('Info.txt', info)
            os.sync()
    except Exception:
        print('Failed to save database "%sExport.b1d" in "%s.b1e"', filepath, zip_filepath)
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

if __name__ == "__main__":
    rows = [float(x[0]) for x in select_samples_table("/home/ubuntu/ftpdata/31_October_2023_13h_39min_Агробит_сортировка/", 1)]
    for i in rows:
        print(i)
