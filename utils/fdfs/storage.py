from django.core.files.storage import FileSystemStorage
from fdfs_client.client import Fdfs_client


class FdfsStorage(FileSystemStorage):
    """自定义文件存储"""

    def _save(self, name, content):
        # path = super()._save(name, content)

        # TODO：保存文件到fdfsdfs服务器
        client = Fdfs_client('utils/fdfs/client.conf')
        try:
            #上传文件到dfs服务器
            datas = content.read()
            result = client.upload_by_buffer(datas)
            # "Remote file_id": "group1/M00/00/00/wKjzh0_xaR63RExnAAAaDqbNk5E1398.py",
            # "Status": "Upload successed.",
            # 获取字典的值
            status = result.get('Status')
            if status == 'Upload successed.':
                # 上传图片成功
                path = result.get('Remote file_id')
            else:
                raise Exception('上传图片失败： %s' % status)
        except Exception as e:
            raise e
        print(path)
        return path

    def url(self, name):
        """返回图片显示时的url地址"""

        url = super().url(name)
        # 拼接上 nginx 的ip和端口，返回完整的图片访问路径
        return 'http://127.0.0.1:8888/' + url