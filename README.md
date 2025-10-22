本项目是基于 https://github.com/zaimatest/SpD1U 的后续开发，相对于旧项目，去除了自动化部分，改为完全调用api的方式对目标进行抓取

使用说明：
1、拉取项目
2、在项目根目录创建 .env 文件：
```
# 默认域名（首次运行或config不存在时使用）
DEFAULT_DOMAIN=
```
3、至少运行一次：
tool/cherk_redirect.py
以更新最新域名
4、修改并运行
#run(测试用).py 
5、抓取成功后，会生成文件保存于 ./WriteBook
6、其余设置可见: ./Spider/setting.py