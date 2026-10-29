class GeneralResponse:
    def success(self, data=[], message="Success", is_cache=False):
        return {
            "success": True,
            "data": data,
            "message": message,
            "cache": "hit" if is_cache else 'miss',
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