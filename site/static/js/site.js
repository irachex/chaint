$(function () {
    $("a[rel=twipsy]").twipsy({
          live: true
    });
    $("a[rel=popover]").popover({
        offset: 10
    }).click(function(e) {
        e.preventDefault()
    });
    $(".alert-message").alert();
    $(".room img, .img-content img").load(function() {
        $(this).css("background","#fff");
    })
});

function submitForm(form) {
	var validate=true;
	$.each($(form+" .required"), function(index, element) {
		if ($(element).val()=="") validate=false;
	});
	if (validate) $(form).submit();
	else {
		$(form + " .msg").fadeIn().delay(2000).fadeOut(2000);
	}
}
