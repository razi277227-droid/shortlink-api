from datetime import datetime
from uuid import uuid4
from sqlalchemy import BigInteger, DateTime, Text, create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
class Base(DeclarativeBase):
    pass
class Link(Base):
    __tablename__ = "links"
    code: Mapped[str] = mapped_column(primary_key=True)
    original_url: Mapped[str]
    clicks: Mapped[int] = mapped_column(BigInteger, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
engine = create_engine("postgresql+psycopg:///shortlink_app_dev")
def run_checks():
    code = "orm_"+uuid4().hex
    rollback_code = "rollback_"+uuid4().hex
    url = "https://example.com/"
    try:
        with Session(engine) as session:
            with session.begin():
                session.add(Link(code=code, original_url=url))
        with Session(engine) as session:
            link = session.get(Link, code)
            assert link is not None
            assert link.original_url == url
            assert link.clicks == 0
            assert link.created_at is not None
        print("прочитали", link.code, link.original_url, link.clicks)
        with Session(engine) as session:
            with session.begin():
                link = session.get(Link, code)
                assert link is not None
                link.clicks += 1
        with Session(engine) as session:
            link = session.get(Link, code)
            assert link is not None
            assert link.clicks == 1
        print("Счетчик увеличился, збс")
        try:
            with Session(engine) as session:
                with session.begin():
                    session.add(Link(code=code, original_url="https://anotherexample.com/"))
        except IntegrityError:
            print("Дубликат запрещен, ок")
        else:
            raise AssertionError("Basa allowed similar codes")
        #исходящая ссылка должна остаться прежней, проверяем
        with Session(engine) as session:
            link = session.get(Link, code)
            assert link is not None
            assert link.code == code
            assert link.original_url == url
            assert link.clicks == 1
        #пробую через комит а не бегин
        with Session(engine) as session:
            link = session.get(Link, code)
            assert link is not None
            session.delete(link)
            session.commit()
        with Session(engine) as session:
            assert session.get(Link, code) is None
        print("Delete - OK")
        #проверим, отменит ли ошибка изменения
        try:
            with Session(engine) as session:
                with session.begin():
                    session.add(Link(code=rollback_code, original_url=url))
                    session.flush()
                    raise RuntimeError("Special error for test")
        except RuntimeError:
            pass
        with Session(engine) as session:
            assert session.get(Link, rollback_code) is None
    finally:
        #even is test were getting bad, delete test codes
        with Session(engine) as session:
            with session.begin():
                for test_code in (code, rollback_code):
                    link = session.get(Link, test_code)
                    if link is not None:
                        session.delete(link)
    print("all test completed, all notes deleted")
if __name__ == "__main__":
    try:
        run_checks()
    finally:
        engine.dispose()




