import logging

def setup(verbose: bool=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s – %(message)s"
    )
    
    # Silenciar loggers de AWS a WARNING para evitar ruido de DEBUG
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Configurar logger de la aplicación
    app_logger = logging.getLogger("is2")
    app_logger.setLevel(level)
    
    return app_logger
