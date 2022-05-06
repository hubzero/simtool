#https://stackoverflow.com/questions/26494747/simple-way-to-choose-which-cells-to-run-in-ipython-notebook-during-run-all/43584169
#https://stackoverflow.com/questions/53204167/is-it-possible-to-combine-magics-in-ipython-jupyter

def detectRankAndSize(line):
   import os
   try:
      mpiRankVar = os.environ['MPI_RANK_VAR']
      rank       = int(os.environ[mpiRankVar])
   except:
      rank = 0
   finally:
      os.environ['APP_MPI_RANK'] = str(rank)

   try:
      mpiSizeVar = os.environ['MPI_SIZE_VAR']
      size       = int(os.environ[mpiSizeVar])
   except:
      size = 0
   finally:
      os.environ['APP_MPI_SIZE'] = str(size)

   return rank,size


def skipRank(rank,cell=None):
   '''Skips execution of the current cell if rank equals 0.'''
   if int(rank) > 0:
      return

   get_ipython().run_cell(cell)


def mpiBarrier(line):
   import os.path
   rank,barrierFile = line.strip().split()
   if int(rank) == 0:
      if not os.path.exists(barrierFile):
         fp = open(barrierFile,'w')
         fp.close()
   else:
      try:
         import time
         while not os.path.exists(barrierFile):
            time.sleep(10)
      except:
         pass


def isMPI(line):
   import os
   try:
      size = int(os.environ['APP_MPI_SIZE'])
   except:
      size = 0

   return size > 0


def load_ipython_extension(ipython):
   '''Registers the skipRank magic when the extension loads.'''
   ipython.register_magic_function(skipRank,'cell')
   ipython.register_magic_function(mpiBarrier,'line')
   ipython.register_magic_function(detectRankAndSize,'line')
   ipython.register_magic_function(isMPI,'line')

def unload_ipython_extension(ipython):
   '''Unregisters the skipRank magic when the extension unloads.'''
   del ipython.magics_manager.magics['cell']['skipRank']
   del ipython.magics_manager.magics['line']['mpiBarrier']
   del ipython.magics_manager.magics['line']['detectRankAndSize']
   del ipython.magics_manager.magics['line']['isMPI']


