import random
import pandas as pd
import matplotlib.pyplot as plt




bottleneck = pd.read_csv("/Users/Chris/JD_MADDPG/maddpg/learning_curves/b1b2used_bottleneck_spread_way2_3000_rewards.csv")
SARNET = pd.read_csv("/Users/Chris/JD_MADDPG/maddpg/learning_curves/SAR_CN3_rewards.csv")
TARMAC = pd.read_csv("/Users/Chris/JD_MADDPG/maddpg/learning_curves/TAR_CN3_rewards.csv")
COMMNET = pd.read_csv("/Users/Chris/JD_MADDPG/maddpg/learning_curves/COMM_CN3_rewards.csv")



plt.plot(bottleneck, label = "jingdi" )
plt.plot(SARNET, label = "SARNET")
plt.plot(TARMAC, label = "TARMAC")
plt.plot(COMMNET, label = "COMMNET")

plt.xticks(fontsize=10)
plt.yticks(fontsize=10)
plt.title("Total Reward Comparison",fontsize=11)
plt.legend(loc='lower right', fontsize=11)
plt.xlabel('Episode',fontsize=11)
plt.ylabel('Total Reward',fontsize=11)
plt.grid(True)


plt.show()