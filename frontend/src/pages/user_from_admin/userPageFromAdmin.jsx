import { useEffect, useState } from "react"
import "./adminpage.css"
import API from "../../utils/api"
import { Link, useNavigate, useParams } from "react-router-dom"
import { useDispatch, useSelector } from "react-redux"
import { setButtonState, setIsBlocked, setMeasures, setPumpIsBroken, setUser } from "../../redux/slice.js"
import classnames from "classnames"
import Chart from "../../components/Chart/chart.jsx"
import { DateTimePicker } from '@mui/x-date-pickers/DateTimePicker';
import { FormControl, InputLabel, MenuItem, Select } from "@mui/material"

function Preloader() {
    return (
        <div className="preloader__container">
            <div id="preloader" className="visible"></div>
        </div>
    )
}

export default () => {
    const navigate = useNavigate()
    const dispatch = useDispatch()
    const { user_id } = useParams()
    console.log(user_id)

    const user = useSelector(state => state.user)
    const measures = useSelector(state => state.user.measures)
    const buttonState = useSelector(state => state.user.buttonState)
    const isBlocked = useSelector(state => state.user.isBlocked)
    const pumpIsBroken = useSelector(state => state.user.pumpBroken)

    const [isLoading, setIsLoading] = useState(true)

    const [startTime, setStartTime] = useState(new Date().getTime() - 24 * 60 * 60 * 1000)
    const [endTime, setEndTime] = useState(new Date().getTime())
    const [step, setStep] = useState("hour")

    const [totalVolume, setTotalVolume] = useState(0)
    const [totalCurrent, setTotalCurrent] = useState(0)
    const [isPaid, setIsPaid] = useState(true)
    const signout = () => {
        localStorage.removeItem("token")
        navigate("/login")
    }

    const onToggleButton = () => {
        if (!isBlocked && !pumpIsBroken) {
            dispatch(setButtonState(!buttonState))
            API
                .post(`/admin/users/${user_id}/toggle_pump`, { "action": buttonState ? "off" : "on" })
                .then(() => { })
                .catch((err) => console.log(err))
        }
    }

    const onBanUnbanUser = () => {
        dispatch(setIsBlocked(!isBlocked))
        API
            .post(`/admin/users/${user_id}/${(!isBlocked) ? "block" : "unblock"}`)
            .then(() => { })
            .catch((err) => console.log(err))
    }

    const onPumpSetBroken = () => {
        dispatch(setPumpIsBroken(!pumpIsBroken))
        API
            .post(`/admin/users/${user_id}/${(!pumpIsBroken) ? "break" : "repair"}`)
            .then(() => { })
            .catch((err) => console.log(err))
    }

    const onPaying = () => {
        API
            .post(`/admin/users/${user_id}/paid`)
            .then(() => { })
            .catch((err) => console.log(err))
    }

    const onGraphRebuild = (type, data) => {
        if (type == 0) {
            setStep(data.target.value)
            API
                .post(`/admin/users/${user_id}/measures`, { start_ts: startTime / 1000, end_ts: endTime / 1000, type: "both", step: data.target.value })
                .then((res) => {
                    console.log(res.data.measures)
                    dispatch(setMeasures(res.data.measures))
                    setTotalVolume(res.data.total_volume)
                    setTotalCurrent(res.data.total_current)
                })
                .catch((err) => console.log(err))
        } else if (type == 1) {
            setStartTime(data)
            API
                .post(`/admin/users/${user_id}/measures`, { start_ts: data / 1000, end_ts: endTime / 1000, type: "both", step })
                .then((res) => {
                    console.log(res.data.measures)
                    dispatch(setMeasures(res.data.measures))
                    setTotalVolume(res.data.total_volume)
                    setTotalCurrent(res.data.total_current)
                })
                .catch((err) => console.log(err))
        } else if (type == 2) {
            setEndTime(data)
            API
                .post(`/admin/users/${user_id}/measures`, { start_ts: startTime / 1000, end_ts: data / 1000, type: "both", step })
                .then((res) => {
                    console.log(res.data.measures)
                    dispatch(setMeasures(res.data.measures))
                    setTotalVolume(res.data.total_volume)
                    setTotalCurrent(res.data.total_current)
                })
                .catch((err) => console.log(err))
        }
    }


    useEffect(() => {
        const time = new Date().getTime()

        API
        .get(`/auth/me`)
        .then((res) => {
            dispatch(setUser(res.data.user))
            if (res.data.user.permissions < 2) {
                navigate("/")
            }
        })
        .catch((err) =>{ 
            console.log(err)
            navigate("/login")
        })

        API
            .post(`/admin/users/${user_id}/measures`, { start_ts: (time - (1000 * 60 * 60 * 24)) / 1000, end_ts: (time + (1000 * 60 * 10)) / 1000, type: "both", step: "hour" })
            .then((res) => {
                dispatch(setMeasures(res.data.measures))
                setTotalVolume(res.data.total_volume)
                setTotalCurrent(res.data.total_current)
            })
            .catch((err) => console.log(err))

        // dispatch(setMeasures(dataset))
    }, [])

    const [flow, setFlow] = useState(0)
    const [current, setCurrent] = useState(0)

    const get_flow_and_current = () => {
        API
            .get("/user/get_cur_data")
            .then((res) => {
                setFlow(res.data.volume)
                setCurrent(res.data.current)
            })
            .catch((err) => console.log(err))
    }

    useEffect(() => {
        setIsLoading(true)
        get_flow_and_current()
        API
            .get(`/admin/users/${user_id}`)
            .then((res) => {
                // dispatch(setUser(res.data.user))
                dispatch(setButtonState(res.data.user.button_state))
                dispatch(setPumpIsBroken(res.data.user.pump_broken))
                dispatch(setIsBlocked(res.data.user.is_blocked))
            })
            .catch((err) => console.log(err))
            .finally(() => setIsLoading(false))

        const intervalId1 = setInterval(get_flow_and_current, 1000)
        return () => {
            clearInterval(intervalId1)
        }
    }, [])

    const savePDF = async () => {
        try {
            const response = await API.post(
                "/pdf/user",
                {
                    start_ts: startTime / 1000,
                    end_ts: endTime / 1000
                }
            );

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;

            const contentDisposition = response.headers['content-disposition'];
            let fileName = 'Отчет.pdf';
            if (contentDisposition && contentDisposition.includes('filename=')) {
                fileName = contentDisposition.split('filename=')[1].split(';')[0];
            }

            link.setAttribute('download', fileName);
            document.body.appendChild(link);
            link.click();

            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Ошибка при скачивании файла:', error);
        }
    }

    if (isLoading) {
        return <Preloader />
    }

    return (
        <div className="user_page">
            <header className="user_page_header">
                <div className="width__container">
                    <div className="left_side">
                        <button className="button dark sign_out" onClick={signout}>
                            <div className="icon__container">
                                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path fillRule="evenodd" clipRule="evenodd" d="M8.37905 2.66859L12.0686 2.08881C15.2892 1.58272 16.8995 1.32967 17.9497 2.22779C19 3.12591 19 4.75596 19 8.01607V10.9996H13.0806L15.7809 7.62428L14.2191 6.37489L10.2191 11.3749L9.71938 11.9996L10.2191 12.6243L14.2191 17.6243L15.7809 16.3749L13.0806 12.9996H19V15.9831C19 19.2432 19 20.8733 17.9497 21.7714C16.8995 22.6695 15.2892 22.4165 12.0686 21.9104L8.37905 21.3306C6.76632 21.0771 5.95995 20.9504 5.47998 20.3891C5 19.8279 5 19.0116 5 17.3791V6.6201C5 4.98758 5 4.17132 5.47998 3.61003C5.95995 3.04874 6.76632 2.92202 8.37905 2.66859Z" fill="#222222" />
                                </svg>
                            </div>
                            <div className="button__text">Выйти</div>
                        </button>
                        {
                            user.permissions > 1 ?
                                <Link to="/admin">
                                    <button className="button dark goto_admin">
                                        <div className="icon__container">
                                            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                                <path fillRule="evenodd" clipRule="evenodd" d="M2.97924 10.2709C4.36454 8.19808 7.26851 5 12 5C16.7314 5 19.6354 8.19808 21.0207 10.2709C21.4855 10.9665 21.718 11.3143 21.6968 11.9569C21.6757 12.5995 21.4088 12.9469 20.8752 13.6417C19.2861 15.7107 16.1129 19 12 19C7.88699 19 4.71384 15.7107 3.12471 13.6417C2.59106 12.9469 2.32424 12.5995 2.30308 11.9569C2.28193 11.3143 2.51436 10.9665 2.97924 10.2709ZM11.9999 16C14.2091 16 15.9999 14.2091 15.9999 12C15.9999 9.79086 14.2091 8 11.9999 8C9.79081 8 7.99995 9.79086 7.99995 12C7.99995 14.2091 9.79081 16 11.9999 16Z" fill="#222222" />
                                            </svg>

                                        </div>
                                        <div className="button__text">Вернуться</div>
                                    </button>
                                </Link>
                                : <></>
                        }
                    </div>

                    <div className="user_info__container">
                        <div className="username">{user.username}</div>
                        <div className="user_role">{(user.permissions > 1) ? "Admin" : "User"}</div>
                    </div>
                </div>
            </header>

            <div className="width__container">
                <div className="managment">
                    <button className={classnames("toggle_button block_user", { "active": !isBlocked })} onClick={onBanUnbanUser} >
                        <div className="icon__container">
                            {isBlocked ?
                                <svg viewBox="0 0 89 89" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M72.182 19.182L13.182 78.182" stroke-width="2" stroke-linecap="round" />
                                    <path d="M58.2168 48.0264C61.0875 48.0264 63.7418 49.5641 64.9229 52.1807C67.0311 56.852 70.0289 64.8528 70.2617 72.9844C70.2775 73.5364 69.8286 73.9844 69.2764 73.9844H23.3789L49.3369 48.0264H58.2168ZM19.332 65.3037C20.4397 60.0618 22.2811 55.3532 23.7129 52.1807C24.8939 49.5641 27.5482 48.0264 30.4189 48.0264H36.6104L19.332 65.3037Z" />
                                    <path d="M44.5 14.833C51.4623 14.833 57.3022 19.6306 58.8994 26.0996L40.9326 44.0664C34.4638 42.4692 29.6671 36.6291 29.667 29.667C29.667 21.4748 36.3078 14.833 44.5 14.833Z" />
                                </svg>
                                :
                                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <circle cx="12" cy="8" r="4" />
                                    <path d="M5.33788 17.3206C5.99897 14.5269 8.77173 13 11.6426 13H12.3574C15.2283 13 18.001 14.5269 18.6621 17.3206C18.79 17.8611 18.8917 18.4268 18.9489 19.0016C19.0036 19.5512 18.5523 20 18 20H6C5.44772 20 4.99642 19.5512 5.0511 19.0016C5.1083 18.4268 5.20997 17.8611 5.33788 17.3206Z" />
                                </svg>
                            }
                        </div>
                        <div className="toggle_text">
                            <div className="header_text">Пользователь</div>
                            <div className="footer_text">{isBlocked ? "Заблокирован" : "Разблокирован"}</div>
                        </div>
                    </button>
                    <button className={classnames("toggle_button broke_pump", { "active": !pumpIsBroken })} onClick={onPumpSetBroken} >
                        <div className="icon__container">
                            {pumpIsBroken ?
                                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path fillRule="evenodd" clip-rule="evenodd" d="M6.58579 5.58579C6 6.17157 6 7.11438 6 9V19C6 20.8856 6 21.8284 6.58579 22.4142C7.17157 23 8.11438 23 10 23H14C15.8856 23 16.8284 23 17.4142 22.4142C18 21.8284 18 20.8856 18 19V9C18 7.11438 18 6.17157 17.4142 5.58579C16.8284 5 15.8856 5 14 5H10C8.11438 5 7.17157 5 6.58579 5.58579ZM8.23431 8.23431C8 8.46863 8 8.84575 8 9.6V15.4C8 16.1542 8 16.5314 8.23431 16.7657C8.46863 17 8.84575 17 9.6 17H14.4C15.1542 17 15.5314 17 15.7657 16.7657C16 16.5314 16 16.1542 16 15.4V9.6C16 8.84575 16 8.46863 15.7657 8.23431C15.5314 8 15.1542 8 14.4 8H9.6C8.84575 8 8.46863 8 8.23431 8.23431Z" />
                                    <path fillRule="evenodd" clip-rule="evenodd" d="M9.29289 1.29289C9 1.58579 9 2.05719 9 3H15C15 2.05719 15 1.58579 14.7071 1.29289C14.4142 1 13.9428 1 13 1H11C10.0572 1 9.58579 1 9.29289 1.29289Z" />
                                </svg>
                                :
                                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M6 9C6 7.11438 6 6.17157 6.58579 5.58579C7.17157 5 8.11438 5 10 5H14C15.8856 5 16.8284 5 17.4142 5.58579C18 6.17157 18 7.11438 18 9V19C18 20.8856 18 21.8284 17.4142 22.4142C16.8284 23 15.8856 23 14 23H10C8.11438 23 7.17157 23 6.58579 22.4142C6 21.8284 6 20.8856 6 19V9Z" />
                                    <path d="M9 3C9 2.05719 9 1.58579 9.29289 1.29289C9.58579 1 10.0572 1 11 1H13C13.9428 1 14.4142 1 14.7071 1.29289C15 1.58579 15 2.05719 15 3V4H9V3Z" />
                                </svg>
                            }
                        </div>
                        <div className="toggle_text">
                            <div className="header_text">Помпа</div>
                            <div className="footer_text">{!pumpIsBroken ? "Работает" : "Не работает"}</div>
                        </div>
                    </button>

                    <button className="toggle_button pay active" onClick={onPaying}>
                        <div className="icon__container">
                            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path fillRule="evenodd" clipRule="evenodd" d="M2.00174 10H21.9983C21.9862 7.82497 21.8897 6.64706 21.1213 5.87868C20.2426 5 18.8284 5 16 5H8C5.17157 5 3.75736 5 2.87868 5.87868C2.1103 6.64706 2.01384 7.82497 2.00174 10ZM22 12H2V14C2 16.8284 2 18.2426 2.87868 19.1213C3.75736 20 5.17157 20 8 20H16C18.8284 20 20.2426 20 21.1213 19.1213C22 18.2426 22 16.8284 22 14V12ZM7 15C6.44772 15 6 15.4477 6 16C6 16.5523 6.44772 17 7 17H7.01C7.56228 17 8.01 16.5523 8.01 16C8.01 15.4477 7.56228 15 7.01 15H7Z" fill="#222222" />
                            </svg>
                        </div>
                        <div className="cur_flow__text">
                            <div className="header_text">Подтвердить</div>
                            <div className="footer_text">Оплату</div>
                        </div>
                    </button>

                </div>
            </div>

            <div className="width__container">
                <div className="managment">
                    <button className={classnames("toggle_button", { "active": buttonState, "disable": isBlocked || pumpIsBroken })} onClick={onToggleButton} >
                        <div className="icon__container">
                            {buttonState ?
                                <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M50 0C77.6142 0 100 22.3858 100 50C100 77.6142 77.6142 100 50 100C22.3858 100 0 77.6142 0 50C0 22.3858 22.3858 0 50 0ZM50 15C30.67 15 15 30.67 15 50C15 69.33 30.67 85 50 85C69.33 85 85 69.33 85 50C85 30.67 69.33 15 50 15Z" />
                                    <path d="M49.2443 50.0909C49.2443 52.4915 48.7827 54.5263 47.8594 56.1953C46.9361 57.8643 45.6861 59.1321 44.1094 59.9986C42.5398 60.8651 40.7784 61.2983 38.8253 61.2983C36.8651 61.2983 35.1001 60.8615 33.5305 59.9879C31.9609 59.1143 30.7145 57.8466 29.7912 56.1847C28.875 54.5156 28.4169 52.4844 28.4169 50.0909C28.4169 47.6903 28.875 45.6555 29.7912 43.9865C30.7145 42.3175 31.9609 41.0497 33.5305 40.1832C35.1001 39.3168 36.8651 38.8835 38.8253 38.8835C40.7784 38.8835 42.5398 39.3168 44.1094 40.1832C45.6861 41.0497 46.9361 42.3175 47.8594 43.9865C48.7827 45.6555 49.2443 47.6903 49.2443 50.0909ZM43.8537 50.0909C43.8537 48.6705 43.6513 47.4702 43.2464 46.4901C42.8487 45.5099 42.2734 44.7678 41.5206 44.2635C40.7749 43.7592 39.8764 43.5071 38.8253 43.5071C37.7813 43.5071 36.8828 43.7592 36.13 44.2635C35.3771 44.7678 34.7983 45.5099 34.3935 46.4901C33.9957 47.4702 33.7969 48.6705 33.7969 50.0909C33.7969 51.5114 33.9957 52.7116 34.3935 53.6918C34.7983 54.6719 35.3771 55.4141 36.13 55.9183C36.8828 56.4226 37.7813 56.6747 38.8253 56.6747C39.8764 56.6747 40.7749 56.4226 41.5206 55.9183C42.2734 55.4141 42.8487 54.6719 43.2464 53.6918C43.6513 52.7116 43.8537 51.5114 43.8537 50.0909ZM70.892 39.1818V61H66.4176L57.7351 48.4077H57.5966V61H52.3232V39.1818H56.8615L65.4482 51.7528H65.6293V39.1818H70.892Z" />
                                </svg>
                                :
                                <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M50 0C77.6142 0 100 22.3858 100 50C100 77.6142 77.6142 100 50 100C22.3858 100 0 77.6142 0 50C0 22.3858 22.3858 0 50 0ZM50 15C30.67 15 15 30.67 15 50C15 69.33 30.67 85 50 85C69.33 85 85 69.33 85 50C85 30.67 69.33 15 50 15Z" />
                                    <path d="M43.2443 50.0909C43.2443 52.4915 42.7827 54.5263 41.8594 56.1953C40.9361 57.8643 39.6861 59.1321 38.1094 59.9986C36.5398 60.8651 34.7784 61.2983 32.8253 61.2983C30.8651 61.2983 29.1001 60.8615 27.5305 59.9879C25.9609 59.1143 24.7145 57.8466 23.7912 56.1847C22.875 54.5156 22.4169 52.4844 22.4169 50.0909C22.4169 47.6903 22.875 45.6555 23.7912 43.9865C24.7145 42.3175 25.9609 41.0497 27.5305 40.1832C29.1001 39.3168 30.8651 38.8835 32.8253 38.8835C34.7784 38.8835 36.5398 39.3168 38.1094 40.1832C39.6861 41.0497 40.9361 42.3175 41.8594 43.9865C42.7827 45.6555 43.2443 47.6903 43.2443 50.0909ZM37.8537 50.0909C37.8537 48.6705 37.6513 47.4702 37.2464 46.4901C36.8487 45.5099 36.2734 44.7678 35.5206 44.2635C34.7749 43.7592 33.8764 43.5071 32.8253 43.5071C31.7813 43.5071 30.8828 43.7592 30.13 44.2635C29.3771 44.7678 28.7983 45.5099 28.3935 46.4901C27.9957 47.4702 27.7969 48.6705 27.7969 50.0909C27.7969 51.5114 27.9957 52.7116 28.3935 53.6918C28.7983 54.6719 29.3771 55.4141 30.13 55.9183C30.8828 56.4226 31.7813 56.6747 32.8253 56.6747C33.8764 56.6747 34.7749 56.4226 35.5206 55.9183C36.2734 55.4141 36.8487 54.6719 37.2464 53.6918C37.6513 52.7116 37.8537 51.5114 37.8537 50.0909ZM46.3232 61V39.1818H61.2166V43.4645H51.5966V47.9389H60.2685V52.2322H51.5966V61H46.3232ZM63.872 61V39.1818H78.7654V43.4645H69.1454V47.9389H77.8173V52.2322H69.1454V61H63.872Z" />
                                </svg>
                            }
                        </div>
                        <div className="toggle_text">
                            <div className="header_text">Состояние помпы</div>
                            <div className="footer_text">{isBlocked ? "Заблокировано" : (pumpIsBroken ? "Сломано" : (buttonState ? "Включено" : "Выключено"))}</div>
                        </div>
                    </button>

                    <div className="management_block cur_current">
                        <div className="icon__container">
                            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path d="M10.4154 18.9231L10.8804 16.5981C10.9357 16.3214 10.9634 16.183 10.8884 16.0915C10.8134 16 10.6723 16 10.3901 16H8.8831C8.49157 16 8.2958 16 8.224 15.8732C8.15219 15.7463 8.25291 15.5785 8.45435 15.2428L10.5457 11.7572C10.7471 11.4215 10.8478 11.2537 10.776 11.1268C10.7042 11 10.5084 11 10.1169 11H7.7215C7.39372 11 7.22984 11 7.15527 10.8924C7.0807 10.7848 7.13825 10.6313 7.25334 10.3244L9.87834 3.32444C9.93719 3.1675 9.96661 3.08904 10.0309 3.04452C10.0951 3 10.1789 3 10.3465 3H15.1169C15.5084 3 15.7042 3 15.776 3.12683C15.8478 3.25365 15.7471 3.42152 15.5457 3.75725L13.4543 7.24275C13.2529 7.57848 13.1522 7.74635 13.224 7.87317C13.2958 8 13.4916 8 13.8831 8H15C15.4363 8 15.6545 8 15.7236 8.1382C15.7927 8.27639 15.6618 8.45093 15.4 8.8L13.6 11.2C13.3382 11.5491 13.2073 11.7236 13.2764 11.8618C13.3455 12 13.5637 12 14 12H15.9777C16.4225 12 16.6449 12 16.7134 12.1402C16.782 12.2803 16.6454 12.4559 16.3724 12.807L11.3003 19.3281C10.7859 19.9895 10.5287 20.3202 10.3488 20.2379C10.1689 20.1556 10.2511 19.7447 10.4154 18.9231Z" />
                            </svg>
                        </div>
                        <div className="cur_current__text">
                            <div className="header_text">Сила тока</div>
                            <div className="footer_text">{current} А</div>
                        </div>
                    </div>

                    <div className="management_block cur_flow">
                        <div className="icon__container">
                            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                <path fillRule="evenodd" clipRule="evenodd" d="M12 21C15.866 21 19 18.1218 19 14.5714C19 10.0507 14.3563 5.21777 12.6333 3.5802C12.2749 3.2395 11.7251 3.2395 11.3667 3.5802C9.64371 5.21777 5 10.0507 5 14.5714C5 18.1218 8.13401 21 12 21ZM9.03367 14.4482C8.99241 14.1752 8.73762 13.9873 8.46458 14.0285C8.19154 14.0698 8.00364 14.3246 8.0449 14.5976C8.17321 15.4468 8.5714 16.2321 9.18058 16.8374C9.78976 17.4427 10.5776 17.8359 11.4275 17.9588C11.7008 17.9983 11.9544 17.8088 11.9939 17.5355C12.0335 17.2622 11.8439 17.0086 11.5706 16.9691C10.9332 16.8769 10.3423 16.582 9.88543 16.1281C9.42855 15.6741 9.1299 15.0851 9.03367 14.4482Z" fill="#33363F" />
                            </svg>
                        </div>
                        <div className="cur_flow__text">
                            <div className="header_text">Водяной поток</div>
                            <div className="footer_text">{flow} л/мин</div>
                        </div>
                    </div>

                </div>
            </div>


            <div className="width__container">
                <div className="filters">
                    <DateTimePicker
                        className="custom-date-time-picker"
                        label="Начало"
                        value={startTime}
                        onChange={(newValue) => { onGraphRebuild(1, new Date(newValue).getTime()) }}
                    />
                    <DateTimePicker
                        label="Конец"
                        value={endTime}
                        onChange={(newValue) => { onGraphRebuild(2, new Date(newValue).getTime()) }}
                    />
                    <FormControl >
                        <InputLabel id="demo-simple-select-label">Шаг</InputLabel>
                        <Select
                            labelId="demo-simple-select-label"
                            id="demo-simple-select"
                            value={step}
                            label="Шаг"
                            onChange={(event) => { onGraphRebuild(0, event) }}
                        >
                            <MenuItem value={"minute"}>Minutes</MenuItem>
                            <MenuItem value={"hour"}>Hours</MenuItem>
                            <MenuItem value={"day"}>Days</MenuItem>
                            <MenuItem value={"week"}>Weeks</MenuItem>
                            <MenuItem value={"month"}>Months</MenuItem>
                        </Select>
                    </FormControl>
                    {/* <button className="build_graphs">Построить</button> */}
                </div>
            </div>

            <div className="width__container" style={{ marginTop: "30px" }}>
                <Chart data={measures} dataKey={"current"} label={"Мощность, Ватт"} colors={["rgb(134, 245, 189)"]} valueFormatter={(e) => `${e} Ватт`} />
                <div className="right_counter">
                    <div className="counter__text">Суммарная мощность:</div>
                    <div className="counter__val">{totalCurrent.toFixed(2)}</div>
                </div>
            </div>
            <div className="width__container">
                <Chart data={measures} dataKey={"volume"} label={"Объем, литр"} colors={["rgb(104, 187, 255)"]} valueFormatter={(e) => `${e} Литр`} />
                <div className="right_counter">
                    <div className="counter__text">Суммарный объем:</div>
                    <div className="counter__val">{totalVolume.toFixed(2)}</div>
                </div>
            </div>
            <div className="button__container" onClick={savePDF}>
                <div className="download_pdf">
                    <div className="_icon__container">
                        <svg viewBox="0 0 256 256" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M33.9464 155.625V245.447C33.9464 250.339 37.9141 254.307 42.8063 254.307H212.907C217.799 254.307 221.767 250.339 221.767 245.447V155.625C158.972 135.952 96.3621 135.831 33.9464 155.625Z" fill="#B83535" />
                            <path d="M221.767 155.625V52.9561C196.381 39.7856 178.81 22.7907 170.217 1.40662H42.8063C37.9141 1.40662 33.9464 5.37434 33.9464 10.2665V155.625H221.767Z" fill="#E9E9E0" />
                            <path d="M221.767 52.9561H178.291C173.831 52.9561 170.217 49.3424 170.217 44.8829V1.40662L221.767 52.9561Z" fill="#D9D7CA" />
                            <path d="M91.6526 177.535H74.9499C72.6204 177.535 70.7349 179.423 70.7349 181.75V209.439V228.401C70.7349 230.728 72.6204 232.616 74.9499 232.616C77.2794 232.616 79.1649 230.728 79.1649 228.401V213.654H91.6526C98.3741 213.654 103.842 208.186 103.842 201.465V189.727C103.842 183.003 98.3741 177.535 91.6526 177.535ZM95.4123 201.462C95.4123 203.533 93.7263 205.222 91.6526 205.222H79.1649V185.962H91.6526C93.7263 185.962 95.4123 187.651 95.4123 189.724V201.462Z" fill="#F9F9F9" />
                            <path d="M130.973 232.613H115.091C112.761 232.613 110.876 230.725 110.876 228.398V181.75C110.876 179.423 112.761 177.535 115.091 177.535H130.973C138.147 177.535 143.983 183.371 143.983 190.545V219.603C143.983 226.777 138.147 232.613 130.973 232.613ZM119.306 224.183H130.973C133.496 224.183 135.553 222.129 135.553 219.603V190.545C135.553 188.022 133.499 185.965 130.973 185.965H119.306V224.183Z" fill="#F9F9F9" />
                            <path d="M180.763 177.535H156.086C153.759 177.535 151.871 179.423 151.871 181.75V228.398C151.871 230.725 153.759 232.613 156.086 232.613C158.413 232.613 160.301 230.725 160.301 228.398V209.288H172.246C174.573 209.288 176.461 207.399 176.461 205.073C176.461 202.746 174.573 200.858 172.246 200.858H160.301V185.962H180.763C183.09 185.962 184.978 184.073 184.978 181.747C184.978 179.42 183.09 177.535 180.763 177.535Z" fill="#F9F9F9" />
                        </svg>
                    </div>
                    <div className="download_pdf__text">
                        Скачать PDF-отчет (не оплачен)
                    </div>
                </div>
            </div>
        </div>
    )
}