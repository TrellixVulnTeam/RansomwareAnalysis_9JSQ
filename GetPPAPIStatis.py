'''
此代码是最开始进行实验时写的代码，创造此算法的几点依据：

1、 父进程具有最大的信息熵

2、 导师也同意此观点

3、 个人认为，在Cuckoo Sandbox的解析报告中，①该进程id(pid)在[processtree]中，且该进程的父进程id（ppid）不在[apistats]中;
                                       ②某进程的children数最多;
                                       则可判断该进程为父进程
    注： 但是若只使用两个方法的其中一个则会出现bug，
    方法①中，未考虑到多个进程树的情况
    →  对于此问题，我曾写过一个算法算是解决了这个bug吧，
        在获取所有进程树的父进程id后，再进行统计所有父进程的子进程数（children），拥有最多子进程的则判定为父进程
        --- children在processtree[i][children]中可获取，调用nested_lookup进行统计，统计原理是统计非空嵌套次数 ---
        于是乎，方法②就生成于方法①的对策中
    方法②中，如上所述，方法②来源于方法①，但若只使用此方法，只能统计到哪个进程拥有最多子进程，但无法断定是否为父进程。
    因此，方法①和②必须同时使用。
但是即便如此，从同一ransomware家族抽取出来的父进程的API种类和个数不尽相同，无法进行Pearson相关系数计算。详细参考2018/9/27-9/28于长崎
参加SPT/IOT研究会的发表资料（存放于OneDrive学校账户中）

'''
#1，将所有实验样本的api统计数据输出到同一个csv文件中，index设置为各个样本的哈希值
#2，再通过遍历文件夹来读取各自的api数据的同时，来筛选需要的api数据
#---------------------------------------------
# 1，一个样本的親プロセス,定义为所有进程树中，children数最多的那个进程。
# 2，example.json ==> behavior ==> processtree ==> processtree[i] ==> children[....]
# 3，条件：①processtree[i]必须有children，②children内容非空，即children中还有其他进程
#父进程的ppid是不在apistats中的
import json
import os
import pandas as pd
from nested_lookup import get_occurrence_of_key #返回嵌套字典中某个key的出现次数

def GetPProcesAPIStats(filepath,apistats_filename):
	list = os.listdir(filepath)
	process_max = {}# 存储list[i]和其对应的json文件的親プロセス的api统计数据
	for i in range(len(list)):
		path = os.path.join(filepath, list[i])
		if os.path.isfile(path):
			with open(path) as jfile:
				process_dict = {}
				jf = json.load(jfile)
				jf_processtree = jf["behavior"]["processtree"]
				for process_id in range(len(jf_processtree)):#当ppid不在apistats，且pid不在["500","388", "496"]之内，则执行取id操作。
					if (((jf_processtree[process_id]["ppid"] in jf["behavior"]["apistats"]) == False)
							and (jf_processtree[process_id]["pid"] in ["500","388", "496"]) == False):
						process_dict[int(jf_processtree[process_id]["pid"])] = get_occurrence_of_key(
							jf_processtree[process_id],"children")
				# process_max[list[i]] = max(process_dict, key=process_dict.get)
				if (process_dict[max(process_dict,key=process_dict.get)] == 0):#当children的数量为零时
					print(process_dict)
					process_max[list[i]] = str(sorted(process_dict.keys(),reverse=True)[0])
				else:#否则取当前的children数最多的id，此时可能会出现多个id拥有最大的children数。所以取其中id最大的（2376：3，1264：3 时取2376）
					print(process_dict)
					maxValue =max(process_dict.values())
					maxValuelist = [k for k, v in process_dict.items() if v == maxValue]
					maxValuelist = sorted(maxValuelist,reverse=True)
					process_max[list[i]] = maxValuelist[0]
				print("Get ", list[i], "'s MaxChildren's process_id ",process_max[list[i]]," ==> complete!!!")

	print(process_max)  # key是文件名，value是各自文件的親プロセス的id。====》{1.json:2376,.......}
	print("##############c#################################################################")
	for maxprocess_id in process_max:
		with open(filepath + "/" + maxprocess_id) as j_file:
			jfname = json.load(j_file)
			print(maxprocess_id, "'s parent process's id is ",process_max[maxprocess_id]," and api calls statistics:")  # Output json file name
			try:
				api_tmp = jfname["behavior"]["apistats"][
					str(process_max[maxprocess_id])]  # 将process_max[maxprocess_id]即进程id转换为字符串进行传值
				df = pd.DataFrame.from_dict(api_tmp, orient="index").T.to_csv(apistats_filename, index=True,
																			  index_label=str(maxprocess_id),
																			  mode="a+")  # mode="a+"表示追加数据，不会覆盖前面的数据
				print(process_max[maxprocess_id], "==> Write to CSV file succeed!!!!!")
			except KeyError:
				print(maxprocess_id,".json ==>",process_max[maxprocess_id]," isn't in apistats")