

class MasterSlaveDBRouter(object):
    """
    数据库主从读写分离路由分发类:没有父类,需实现下面三个方法
    """

    def db_for_read(self, model, **hints):
        """读数据库:查询"""
        return "slave"

    def db_for_write(self, model, **hints):
        """写数据库:增,删,改"""
        return "default"

    def allow_relation(self, obj1, obj2, **hints):
        """是否运行关联操作:inner join.../ user.address_set..."""
        return True