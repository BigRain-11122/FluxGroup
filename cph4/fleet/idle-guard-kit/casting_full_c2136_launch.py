# -*- coding: utf-8 -*-
# casting_full_c2136_launch.py -- bank entry point for the Xingqing casting full-res stage.
# The runner reads XQ_CAST_FULL from the environment; a scheduled/idle-guard launch has a clean
# environment, so this launcher sets the flag and then executes the proven runner as __main__.
import os
import runpy

os.environ["XQ_CAST_FULL"] = "1"
runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "xq_casting_c2136.py"),
               run_name="__main__")