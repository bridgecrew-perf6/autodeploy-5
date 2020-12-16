
""" Message format:
        repo-name \\n
        branch:hashofoldstate:hashofnewstate \\n
        username:person-name:email
"""

def encode_message(json: dict) -> bytes:
    p = json['pusher']
    n = json['repository']['full_name']
    refstr = f"{json['ref']}:{json['before']}:{json['after']}\n{json['']}"
    pusherstr = f"{p['login']}:{p['full_name']}:{p['email']}"
    return f"{n}\n{refstr}\n{pusherstr}".encode('utf8')


class Message(object):

    repo:     str
    branch:   str
    before:   str
    current:  str
    pusher:   str
    fullname: str
    email:    str

    @classmethod
    def from_msg(cls, msg: bytes):
        c = cls()
        c.repo, ref, person = msg.decode('utf8').split('\n')
        c.branch, c.before, c.current = ref.split(':')
        c.pusher, c.fullname, c.email = person.split(':')
        return c


if __name__ == "__main__":
    msg = b'refs/heads/xxx:123abc:456ffe\nwillsk:William Strecker-Kellogg:willsk@bnl.gov'
    m = Message.from_msg(msg)
