import { useState } from "react"
import "./registerpage.css"
import { Link, useNavigate } from "react-router-dom"
import classnames from "classnames"
import API from "../../utils/api.js"
import VideoCaprure from "../../components/videoCaprute/videoCapture.jsx"

export default () => {
    const navigate = useNavigate()

    const [state, setState] = useState(0)

    const [login, setLogin] = useState("")
    const [password, setPassword] = useState("")
    const [buildingId, setBuildingId] = useState(null)
    const [flatId, setFlatId] = useState(null)

    const [isLoginError, setIsLoginError] = useState(false)
    const [isPasswordError, setIsPasswordError] = useState(false)
    const [isBuildingIdError, setIsBuildingIdError] = useState(false)
    const [isFlatIdError, setIsFlatIdError] = useState(false)
    const [errorText, setErrorText] = useState("")

    const onRegisterHandler = () => {
        if (login.length <= 3) {
            setIsLoginError(true)
            setErrorText("Длина логина должна быть больше 3 символов!")
            return
        } else if (password.length < 8) {
            setIsPasswordError(true)
            setErrorText("Длина пароля должна быть больше 7 символов!")
            return
        } else if (!buildingId) {
            setIsBuildingIdError(true)
            setErrorText("Номер здания не может быть пустым!")
            return
        } else if (!flatId) {
            setIsFlatIdError(true)
            setErrorText("Номер квартиры не может быть пустым!")
            return
        }
        // else if (buildingId == 2 && flatId == 4) {
        //     setIsFlatIdError(true)
        //     setErrorText("Квартиры 5 в 3 доме не существует!")
        //     return
        // }

        setState(1)
    }

    const onRegisterHandlerWithCapture = (data) => {
        API
            .post("/auth/register", { image: data, additionalData: { login, password, building_id: buildingId - 1, flat_id: flatId - 1 } }, { headers: { 'Content-Type': 'application/json' } })
            .then((res) => {
                localStorage.setItem("token", res.data.token)
                navigate("/")
            })
            .catch((err) => console.log(err))
    }

    const onLoginEnter = (e) => {
        setIsLoginError(false)
        setIsPasswordError(false)
        setIsBuildingIdError(false)
        setIsFlatIdError(false)
        setErrorText("")
        setLogin(e.target.value.trim().replace(/[^a-zA-Z0-9@._]/g, ""))
    }

    const onPasswordEnter = (e) => {
        setIsLoginError(false)
        setIsPasswordError(false)
        setIsBuildingIdError(false)
        setIsFlatIdError(false)
        setErrorText("")
        setPassword(e.target.value.trim().replace(/[^a-zA-Z0-9]/g, ""))
    }

    const onBuildingIdEnter = (e) => {
        setIsLoginError(false)
        setIsPasswordError(false)
        setIsBuildingIdError(false)
        setIsFlatIdError(false)
        setErrorText("")
        const val = e.target.value.trim().replace(/[^1-3]/g, "").slice(0, 1)
        setBuildingId(val)
        e.target.value = val
    }

    const onFlatIdEnter = (e) => {
        setIsLoginError(false)
        setIsPasswordError(false)
        setIsBuildingIdError(false)
        setIsFlatIdError(false)
        setErrorText("")
        const val = e.target.value.trim().replace(/[^1-5]/g, "").slice(0, 1)
        setFlatId(val)
        e.target.value = val
    }

    return (
        <div className="auth_page">
            <div className="auth_page__container">
                {state === 0 ?
                    <>
                        <h1 className="auth_page__title">Регистрация</h1>
                        <form className="auth_form">
                            <input type="text" className={classnames("auth__input", { "error": isLoginError })} placeholder="Логин" onChange={onLoginEnter} value={login} />
                            <input type="password" className={classnames("auth__input", { "error": isPasswordError })} placeholder="Пароль" onChange={onPasswordEnter} value={password} />
                            <input type="building_id" className={classnames("auth__input", { "error": isBuildingIdError })} placeholder="Номер здания (1-3)" onChange={onBuildingIdEnter} />
                            <input type="flat_id" className={classnames("auth__input", { "error": isFlatIdError })} placeholder="Номер квартиры (1-5)" onChange={onFlatIdEnter} />
                            <div className={classnames("dropdown", { "active": errorText.length != 0 })}>
                                <div className="dropdown__container">
                                    <div className="error__text">{errorText}</div>
                                </div>
                            </div>
                            <button className="auth__submit" onClick={e => { e.preventDefault(); onRegisterHandler() }}>Зарегистрироваться</button>
                        </form>
                    </>
                    :
                    <>
                        <h1 className="auth_page__title">Сделайте фото</h1>
                        <VideoCaprure onSendHandler={onRegisterHandlerWithCapture} />
                    </>
                }
                <Link to="/login" className="auth__change" >Войти</Link>
            </div>
        </div>
    )
}