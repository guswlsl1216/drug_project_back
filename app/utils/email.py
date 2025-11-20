from flask_mail import Message
from app import mail

def send_inquiry_answer_email(to_email, title, answer):
  """고객센터 문의 답변 이메일 발송"""
  msg = Message(
    subject=f"[문의답변] {title}",
    recipients=[to_email]
  )
  msg.body = (
    f"안녕하세요, 고객님.\n"
    f"문의하신 내용에 대한 답변입니다.\n\n"
    f"------------------------------------\n"
    f"문의 제목: {title}\n\n"
    f"관리자 답변:\n{answer}\n"
    f"------------------------------------\n\n"
    f"궁금하신 점이 있으면 언제든 다시 문의해주세요.\n"
    f"감사합니다."
  )

  mail.send(msg)

