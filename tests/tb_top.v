`timescale 1ns/1ps
module tb;
    reg clk=0;
    wire led;
    fpga_top dut(.clk(clk),.led(led));
    always #5 clk=~clk;
    integer cycle,elapsed,phase,stage,duty,expected;
    integer checks=0,periods=0,high_count=0,seen[0:4],i;
    initial begin
        for(i=0;i<5;i=i+1)seen[i]=0;
        // Full production configuration: traverse all five stages and wrap.
        // The test time scale does not change the real 12 MHz timing constraint.
        for(cycle=1;cycle<=5243400;cycle=cycle+1)begin
            @(posedge clk);#1;
            elapsed=(cycle>7)?cycle-7:0;
            phase=elapsed%256;
            stage=(elapsed/1048576)%5;
            duty=64*stage;
            expected=(cycle>7 && phase<duty);
            if(led!==expected[0])begin
                $display("PWM_TOP_MISMATCH cycle=%0d elapsed=%0d phase=%0d stage=%0d got=%b expected=%b",cycle,elapsed,phase,stage,led,expected[0]);
                $fatal(1,"PWM top independent sample mismatch");
            end
            checks=checks+1;
            if(cycle>7)begin
                if(phase==0)high_count=0;
                if(led)high_count=high_count+1;
                if(phase==255 && elapsed>=256)begin
                    if(high_count!=duty)$fatal(1,"PWM top period duty mismatch");
                    checks=checks+1;periods=periods+1;seen[stage]=seen[stage]+1;
                end
            end
        end
        for(i=0;i<5;i=i+1)begin
            if(seen[i]==0)$fatal(1,"PWM top stage not exercised");
            $display("PWM_TOP_STAGE stage=%0d duty=%0d full_periods=%0d",i,64*i,seen[i]);
        end
        $display("PWM_TOP_PASS cycles=5243400 checks=%0d full_periods=%0d",checks,periods);
        $finish;
    end
endmodule
