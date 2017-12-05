/*
*  Script for sponsor project household details expand to see all the household numbers.
*  Used only in the list view of sponsor project details
*/


function more_click(element){
    $(element).parent().parent().hide();
    $(element).parent().parent().parent().find('div.lesslist').show();
}
function less_click(element){
    $(element).parent().parent().hide();
    $(element).parent().parent().parent().find('div.morelist').show();
}
$(document).ready(function(){

    function update_view(){
        if($('#result_list').length > 0){
            $.each($('.field-household_code'), function(index, house){
                houses = $(house).html();
                $(house).html("<div class='lesslist' style='display:none;'>"+houses+"&nbsp;&nbsp;<b><a onclick='less_click(this);'>Less</a></b></div>");
                $(house).append("<div class='morelist'>"+houses.split(',').splice(0,10).join()+" ...<b><a onclick='more_click(this);'>More</a></b></div>");
            });
        }
    }

    update_view();

    //$("textArea[name=household_code], div.field-household_code p.help").addClass('hide');
    //var household = $("textArea[name=household_code]").val();
    //$("textArea[name=household_code]").parent().append('<p class="householdcode">'+household+'</p>');
    //$("input[name=_save]").click(function(){
    //    var data = "";
    //    $.each($("td.field-household_code"), function(index, element){
    //           var d = $(element).find('textArea').val();
    //           if (d != "")
    //           {
    //                data += d.slice(d.indexOf('[')+1, d.indexOf(']')) + ',';
    //           }
    //   });
    //    $("textArea[name=household_code]").val("["+data.slice(0,data.length-1)+"]");
    //});

});
