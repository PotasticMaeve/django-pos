class GeneralResponse:
    def success(self, data=[], message="Success"):
        return {
            "success": True,
            "data": data,
            "message": message,
            "meta": {
                "total": len(data) if data is not None else 0
            }
        }   

    def error(self, message="Error", data=[]):
        return {
            "success": False,
            "data": data,
            "message": message,
            "meta": {
                "total": len(data) if data is not None else 0
            }
        }