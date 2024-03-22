# 3. Benchmarking and Profiling

## Introduction

The benchmarking is essential to the progress and success of the project. Also, benchmarking code is a essential part of software development and it's a software best practice. It can't keep implementing new features without ensuring that what have been done. With benchmarking, we can confirm that our software does what it's supposed to, and that it can handle most of the cases.

## Memory Profiler

Echoshader uses Time-based memory usage in [Memory Profiler](https://pypi.org/project/memory-profiler/) to execute benchmarking. This is a python module for monitoring memory consumption of a process as well as line-by-line analysis of memory consumption for python programs. It is a pure python module which depends on the [psutil](http://pypi.python.org/pypi/psutil) module.

Testing code, results and exporting HTMLs have been posted on [Google Drive](https://drive.google.com/drive/folders/1z9nUWZe8N6_AEbi2hDgp-isOfTn11J-P?usp=sharing).

- [1 day with 1 min along ping_time, 1 m for depth (OOI 2017 Aug)](https://drive.google.com/drive/folders/19_Wd1ugIsrMBjJbi8tnHdq-E55LpRMty?usp=sharing)

  ![image-20220906212522202](https://drive.google.com/uc?export=view&id=19iOsymkZeggkY47VLF7wWV-oWNz0Hgb5)

  ![image-20220906212522202](https://drive.google.com/uc?export=view&id=12DTAIHJGz9L98HsmhpmYWnwh9ceM2YT8)

- [1 day with 10 min along ping_time, 5 m for depth (Hake Survey)](https://drive.google.com/drive/folders/116WhBXQRJFT1jzmZhD_T6RaP5jKRMo35?usp=sharing)

  ![image-20220906212522202](https://drive.google.com/uc?export=view&id=1PPRC8WBVnesTlD9YLSML7WFh7W-DYfQk)

  ![image-20220906212522202](https://drive.google.com/uc?export=view&id=15Rl_IZojMccoG2O6UnJt8LeQiorUMCBq)

  ![image-20220906212522202](https://drive.google.com/uc?export=view&id=1Qub7f69512fNupCLtEVVNl8DNeYDxu-2)

- [30 days with 30 mins along ping_time, 1 m for depth (OOI 2017 Aug)](https://drive.google.com/drive/folders/1caGwWmeMOjgi51R9fMKi7XcLx0tAeZOz?usp=sharing)

  ![image-20220906212522202](https://drive.google.com/uc?export=view&id=1igXPkVapAGXYuYrF83uZ2bhUSILKRsmc)

  ![image-20220906212522202](https://drive.google.com/uc?export=view&id=1KtgLTeES3iwgx77vWQAY-pHwEWo8MC3N)

- [10 days with 30 mins along ping_time, 5 m for depth (Hake Survey)](https://drive.google.com/drive/folders/1t53cGzFNLh16bAgzdoAHH2tIk3Gjo9ma?usp=sharing)

  ![image-20220906212522202](https://drive.google.com/uc?export=view&id=1Zm0jxlEhAY6t9VyWm9G_xEj3Bm3YamKH)

  ![image-20220906212522202](https://drive.google.com/uc?export=view&id=1NQWyhUyZuAv0YNvzt2h1GTOwaYCh0Fh5)

  ![image-20220906212522202](https://drive.google.com/uc?export=view&id=1ub_izrSg5PuPGzURak4VIcerp0WwybkN)

- [2 hr in raw resolution (with 1 sec along ping_time, 0.2 m for depth) (OOI 2017 Aug)](https://drive.google.com/drive/folders/1a5Euv5NdRcKqwh8l8h_YuGKqz0_Zxjf6?usp=sharing)

  ![image-20220906212522202](https://drive.google.com/uc?export=view&id=1Dr7k6NY1o4r-uamCP14leXi44AXcoD9h)

  ![image-20220906212522202](https://drive.google.com/uc?export=view&id=1kT9ecVqbTZNDPLjT8ljn8x3bAjJ6RRZW)

- [2 hr in raw resolution  (with 2 secs along ping_time, 0.2 m for depth) (hake survey)](https://drive.google.com/drive/folders/1Xem6ugZGfIS54Ov_V9diblaqBZOb0JAr?usp=sharing)

  ![image-20220906212522202](https://drive.google.com/uc?export=view&id=1VaiuU3IvYmsHTLZmd6N0o57xJErgn-Uk)

  ![image-20220906212522202](https://drive.google.com/uc?export=view&id=1l1A6Hy71A-2CE-Xdm9tRQvDDTnXYT96L)

  ![image-20220906212522202](https://drive.google.com/uc?export=view&id=1ieELLYysjY0l7HLQk77RzlCB90bqN3uR)

## Admin Panel

Also, we can take use of [Admin Panel](https://panel.holoviz.org/user_guide/Performance_and_Debugging.html#admin-panel) in Panel library.

The `/admin` panel provides an overview of the current application and provides tools for debugging and profiling. It can be enabled by passing the `--admin` argument to the `panel serve` command.

For example, we build a new testing file called 'your_file_name.py' or 'your_file_name.ipynb' below:

```python
import xarray as xr
from pathlib import Path

from echoshader import echogram

MVBS_ds = xr.open_mfdataset(
    str('test_admin.nc'),
    data_vars='minimal', coords='minimal',
    combine='by_coords'
)

pn = echogram.panel

echogram = echogram.Echogram(MVBS_ds)

pn.Row(echogram.widgets, echogram.view_gram).servable()
```

Don't forget to use `.servable()` to specify which component you want to display in the browser.

Then we input below command in `cmd Prompt`  or `Anaconda Prompt` to start up the server:

```bash
panel serve --admin --profiler=snakeviz your_file_name.py
```

Users should use the commandline `--admin` and `--profiler` options. Don't forget to specify the profiler.

Once enabled the server, input below urls to open procedure page and admin page:

```bash
http://localhost:your_port_number/your_file_name
```

```bash
http://localhost:your_port_number/admin
```

The overview page provides some details about currently active sessions, running versions and resource usage (if `psutil` is installed).

![image-20220906212522202](https://drive.google.com/uc?export=view&id=1h3_b2zlE7h9_wlU-9fopRzofk6xB3IrA)

The launch profiler profiles the execution time of the initialization of a particular application. It can be enabled by setting a profiler using the commandline `--profiler` option. Available profilers include:

- [`pyinstrument`](https://pyinstrument.readthedocs.io/): A statistical profiler with nice visual output

- [`snakeviz`](https://jiffyclub.github.io/snakeviz/): SnakeViz is a browser based graphical viewer for the output of Python’s cProfile module and an alternative to using the standard library pstats module.

Once enabled the launch profiler will profile each application separately and provide the profiler output generated by the selected profiling engine.

![image-20220906212522202](https://drive.google.com/uc?export=view&id=1vfHgH4FVbSrirjTxv4X8E_UR5lJmRLCm)
