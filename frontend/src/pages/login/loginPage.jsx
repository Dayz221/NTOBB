import { useState } from "react"
import "./loginpage.css"
import { Link, useNavigate } from "react-router-dom"
import classnames from "classnames"
import API from "../../utils/api"
import VideoCapture from "../../components/videoCaprute/videoCapture.jsx"

export default () => {
    const navigate = useNavigate()

    const [login, setLogin] = useState("")
    const [password, setPassword] = useState("")

    const [isError, setIsError] = useState(false)
    const [loginState, setLoginState] = useState(0)
    const [response, setResponse] = useState("")

    const onSemiLoginHandler = () => {
        API
            .post("/auth/semi_login", { login, password })
            .then((res) => {
                setLoginState(1)
            })
            .catch((err) => setIsError(true))
    }

    const onLoginHandler = (photo) => {
        API
            .post("/auth/login", { image: photo, additionalData: { login, password }})
            .then((res) => {
                localStorage.setItem("token", res.data.token)
                navigate("/")
            })
            .catch((err) => {console.log(err); setResponse("error")})
    }

    const onLoginEnter = (e) => {
        setIsError(false)
        setLogin(e.target.value.trim().replace(/[^a-zA-Z0-9@._]/g, ""))
    }

    const onPasswordEnter = (e) => {
        setIsError(false)
        setPassword(e.target.value.trim().replace(/[^a-zA-Z0-9]/g, ""))
    }

    return (
        <div className="auth_page login_page">
            <div className="auth_page__container">
                {loginState === 0 ?
                    <>
                        <h1 className="auth_page__title">Вход</h1>
                        <form className="auth_form">
                            <input type="text" className={classnames("auth__input", { "error": isError })} placeholder="Логин" onChange={onLoginEnter} value={login} />
                            <input type="password" className={classnames("auth__input", { "error": isError })} placeholder="Пароль" onChange={onPasswordEnter} value={password} />
                            <button className="auth__submit" onClick={e => { e.preventDefault(); onSemiLoginHandler() }}>Войти</button>
                        </form>
                    </>
                    :
                    <>
                        <h1 className="auth_page__title">Распознавание лица</h1>
                        <VideoCapture setResponse={setResponse} response={response} onSendHandler={onLoginHandler}/>
                    </>
                }
                <Link to="/register" className="auth__change">Зарегистрироваться</Link>
            </div>
        </div>
    )
}