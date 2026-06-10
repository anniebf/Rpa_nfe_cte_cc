from anticaptchaofficial.imagecaptcha import *
def anticaptcha():
    solver = imagecaptcha()
    solver.set_verbose(1)
    solver.set_key("174d6da17fc9ea20b644ed5b591ff5d9")
    

    # Specify softId to earn 10% commission with your app.
    # Get your softId here: https://anti-captcha.com/clients/tools/devcenter
    solver.set_soft_id(0)

    captcha_text = solver.solve_and_return_solution(fr'img\captcha.jpg')
    if captcha_text != 0:
        print("o captcha foi resolvido corretamente")

    return captcha_text
