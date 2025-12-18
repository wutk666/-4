class Config:
    SECRET_KEY = 'change-me'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///xss_defense.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    XSS_DEFENSE_ENABLED = True
    # 其他配置（比如日志、IP白名单等）