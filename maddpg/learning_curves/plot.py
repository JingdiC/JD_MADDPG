import random
import pandas as pd
import matplotlib.pyplot as plt





full = (pd.read_csv("/Users/chenjingdi/Desktop/code/Jingdi-MADDPG/maddpg/learning_curves/full_ob_full_comm_3000_rewards.csv")).to_numpy().flatten().tolist()
comm = pd.read_csv("/Users/chenjingdi/Desktop/code/Jingdi-MADDPG/maddpg/learning_curves/Jingdi_3000_rewards.csv")


plt.plot(full, label = "full_ob_full_comm")
plt.plot(comm, label = "po_limited comm")
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)
plt.title("Total Reward Comparison",fontsize=11)
plt.legend(loc='lower right', fontsize=11)
plt.xlabel('Episode',fontsize=11)
plt.ylabel('Total Reward',fontsize=11)
plt.grid(True)


plt.show()