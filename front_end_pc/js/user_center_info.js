var vm = new Vue({
    el: '#app',
    data: {
        host,
        user_id: sessionStorage.user_id || localStorage.user_id,
        token: sessionStorage.token || localStorage.token,
        username: '',
        mobile: '',
        email: '',
        email_active: false,
        set_email: false,
        send_email_btn_disabled: false,
        send_email_tip: '重新发送验证邮件',
        email_error: false,
        histories: []
    },
    mounted: function(){
        // 页面一加载便向后端请求:判断用户的登录状态
        if (this.user_id && this.token) {
            axios.get(this.host + '/user/', {
                    // 向后端传递JWT token的方法
                    headers: {
                        'Authorization': 'JWT ' + this.token
                    },
                    responseType: 'json',
                })
                .then(response => {
                    // 加载用户数据
                    this.user_id = response.data.id;
                    this.username = response.data.username;
                    this.mobile = response.data.mobile;
                    this.email = response.data.email;
                    this.email_active = response.data.email_active;

                    // 用户已登录,则补充请求浏览历史
                    axios.get(this.host + '/browse_histories/', {
                            headers: {
                                // 携带JWT token
                                'Authorization': 'JWT ' + this.token
                            },
                            responseType: 'json'
                        })

                        // 请求成功则给history赋值数据,
                        .then(response => {
                            this.histories = response.data;
                            // 此时history是一个字典列表,[{"url": "..."}, {"":""}]
                            for(var i=0; i<this.histories.length; i++){
                                this.histories[i].url = '/goods/' + this.histories[i].id + '.html';
                            }
                        })

                })
                .catch(error => {
                    if (error.response.status==401 || error.response.status==403) {
                        location.href = '/login.html?next=/user_center_info.html';
                    }
                });
        } else {
            location.href = '/login.html?next=/user_center_info.html';
        }
    },
    methods: {
        // 退出
        logout: function(){
            sessionStorage.clear();
            localStorage.clear();
            location.href = '/login.html';
        },

        // 设置email
        save_email: function(){
            var re = /^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$/;
            if(re.test(this.email)) {
                this.email_error = false;
            } else {
                this.email_error = true;
                return;
            }
            // 发送put请求,对应UpdateAPIView类的update方法
            axios.put(this.host + '/email/',
                // 请求体数据
                { email: this.email },
                // 本次请求的配置信息
                {
                    headers: {
                        // JWT 要求的固定格式
                        'Authorization': 'JWT ' + this.token
                    },
                    responseType: 'json'  // 指明需要返回json数据
                })
                .then(response => {
                    this.set_email = false;
                    this.send_email_btn_disabled = true;
                    this.send_email_tip = '已发送验证邮件'
                })
                .catch(error => {
                    alert(error.data);
                });
        }
    }
});