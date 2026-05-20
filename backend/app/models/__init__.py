# ORM 模型包
# 存放所有数据库表对应的 SQLAlchemy 模型类
# 后续会创建：tenant.py、user.py、knowledge_base.py、document.py 等
#
# ⚠️ 重要：当所有模型文件创建完成后，必须在这里导入所有模型类
# 这样 Alembic 才能通过 Base.metadata 自动发现所有表，生成迁移脚本
# 例如：
# from app.models.tenant import Tenant
# from app.models.user import User