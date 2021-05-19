import random
import pandas as pd
import matplotlib.pyplot as plt



jingdi_bw1 = pd.read_csv("/Users/Chris/JD_MADDPG/maddpg/learning_curves/jingdi_bw1_spread_6_600_rewards.csv")
#bottleneck_bw100 = pd.read_csv("/Users/Chris/JD_MADDPG/maddpg/learning_curves/bw100_b1b2used_bottleneck_spread_way2_600_rewards.csv")

SARNET_bw1 = pd.read_csv("/Users/Chris/JD_MADDPG/maddpg/learning_curves/SAR_6agents_bw1_rewards.csv")
#SARNET_bw100 = pd.read_csv("/Users/Chris/JD_MADDPG/maddpg/learning_curves/SAR_6agents_bw100_rewards.csv")

#TARMAC_bw1 = pd.read_csv("/Users/Chris/JD_MADDPG/maddpg/learning_curves/bw1_TAR_CN3_rewards.csv")
#TARMAC_bw100 = pd.read_csv("/Users/Chris/JD_MADDPG/maddpg/learning_curves/bw100_TAR_CN3_rewards.csv")

#COMMNET = pd.read_csv("/Users/Chris/JD_MADDPG/maddpg/learning_curves/COMM_CN3_rewards.csv")



plt.plot(jingdi_bw1, label = "jingdi_bw1" )
#plt.plot(bottleneck_bw100, label = "jingdi_bw100" )

plt.plot(SARNET_bw1, label = "SARNET_bw1")
#plt.plot(SARNET_bw100, label = "SARNET_bw100")

#plt.plot(TARMAC_bw1, label = "TARMAC_bw1")
#plt.plot(TARMAC_bw100, label = "TARMAC_bw100")


#plt.plot(COMMNET, label = "COMMNET")

plt.xticks(fontsize=10)
plt.yticks(fontsize=10)
#plt.ylim(-400,-300)
plt.title("Total Reward Comparison",fontsize=11)
plt.legend(loc='lower right', fontsize=11)
plt.xlabel('Episode',fontsize=11)
plt.ylabel('Total Reward',fontsize=11)
plt.grid(True)


plt.show()