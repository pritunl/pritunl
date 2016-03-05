from pritunl.utils.request import get

def get_ami_id():
    try:
        resp = get(
            'http://169.254.169.254/latest/meta-data/ami-id',
            timeout=0.5,
        )

        if resp.status_code != 200:
            return

        return resp.content
    except:
        pass
