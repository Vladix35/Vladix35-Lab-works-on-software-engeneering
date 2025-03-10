workspace "Conference_organisation" {

    !identifiers hierarchical
    
    model {
        user = person "Пользователь"
        conference_organisation = softwareSystem "Conference Organisation System" {
            
            description "Веб-приложение для организации конференций"

            db = container "База данных" {
                description "База данных для хранения информации о слушателях/докладчиках/конференциях"
                technology "MySQL"
                tags "Database"
                
            }

            user_control = container "Система контроля пользователей" {
                description "Регистрация и управление всеми пользователями"
                technology "Spring Boot"
                conference_user = component "Conference User"
                login = component "Login"
                first_name = component "First Name"
                last_name = component "Last Name"
                mask = component "Mask"
                conference_user -> db "Создание нового пользователя или поиск существующего"
                login -> db "Создание логина нового пользователя или поиск существующего"
                first_name -> db "Создание имени нового пользователя или поиск существующего"
                last_name -> db "Создание фамилии нового пользователя или поиск существующей"
                mask -> db "Создание маски нового пользователя или поиск существующей"
            }

            report_control = container "Система контроля докладов" {
                description "Создание и управление всеми докладами"
                technology "Spring Boot"
                report = component "Report"
                report -> db "Создание нового доклада/поиск существующего"
            }

            conference_control = container "Система контроля конференций" {
                description "Создание и управление всеми конференциями"
                technology "Spring Boot"
                conference = component "Conference"
                conference -> db "Создание новой конференции/поиск существующей"
            }

            web_interface = container "Веб-интерфейс" {
                description "Пользовательский интерфейс для проведения конференции"
                technology "React"
                -> user_control
                -> report_control
                -> conference_control
                -> db "Получение данных об конференции"
            }
        }

        user -> conference_organisation.web_interface "Взаимодействие с конференцией через платформу"
    }

    views {
        systemContext conference_organisation {
            include *
            autolayout lr
        }

        container conference_organisation {
            include *
            autolayout lr
        }

        dynamic conference_organisation {
            title "Создание пользователя"
            user -> conference_organisation.web_interface "Заполнение формы регистрации"
            conference_organisation.web_interface -> conference_organisation.user_control "POST /conference_user"
            conference_organisation.user_control -> conference_organisation.db "Сохранение данных"
        }

        dynamic conference_organisation {
            title "Поиск пользователя по логину"
            user -> conference_organisation.web_interface "Ввод логина"
            conference_organisation.web_interface -> conference_organisation.user_control "GET /conference_user?login={value}"
            conference_organisation.user_control -> conference_organisation.db "Поиск в базе данных"
        }

        dynamic conference_organisation {
            title "Поиск пользователя по имени/фамилии"
            user -> conference_organisation.web_interface "Ввод имени/фамилии"
            conference_organisation.web_interface -> conference_organisation.user_control "GET /conference_user?name={mask}"
            conference_organisation.user_control -> conference_organisation.db "Фильтрация пользователей"
        }

        dynamic conference_organisation {
            title "Добавление доклада в конференцию"
            user -> conference_organisation.web_interface "Создание доклада"
            conference_organisation.web_interface -> conference_organisation.report_control "POST /report"
            conference_organisation.report_control -> conference_organisation.db "Сохранение доклада"
            conference_organisation.web_interface -> conference_organisation.conference_control "POST /conference/report"
            conference_organisation.conference_control -> conference_organisation.db "Обновление конференции"
        }

        dynamic conference_organisation {
            title "Получение списка всех докладов"
            user -> conference_organisation.web_interface "Запрос списка докладов"
            conference_organisation.web_interface -> conference_organisation.report_control "GET /report"
            conference_organisation.report_control -> conference_organisation.db "Получение всех записей"
        }

        dynamic conference_organisation {
            title "Поиск докладов в конференции"
            user -> conference_organisation.web_interface "Просмотр конференции"
            conference_organisation.web_interface -> conference_organisation.conference_control "GET /conference/report"
            conference_organisation.conference_control -> conference_organisation.db "Получение списка докладов"
        }
        
        styles {

            element "Person" {
                background #03AF03
                shape person
            }

            element "Software System"  {
                background #267FC7
            }

            element "Container" {
                background #55aa55
            }
            
            element "Database" {
                shape cylinder
            }
        }
    }
}
